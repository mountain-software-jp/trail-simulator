import pandas as pd
import numpy as np
import argparse
import json

def define_course_capacity(course_df, single_track_sections):
    """Adds a 'capacity' column to the course data DataFrame."""
    # Default to a wide path (high capacity)
    course_df['capacity'] = 1000 
    
    for section in single_track_sections:
        start_km, end_km, capacity = section['range_km'][0], section['range_km'][1], section['capacity']
        start_m, end_m = start_km * 1000, end_km * 1000
        # Set the capacity for the specified section
        course_df.loc[(course_df['distance'] >= start_m) & (course_df['distance'] <= end_m), 'capacity'] = capacity
        print(f"Set single track with capacity {capacity} from {start_km}km to {end_km}km.")
    return course_df

def run_congestion_simulation(num_runners, avg_pace_min_per_km, std_dev_pace, time_limit_hours, course_df, wave_groups, wave_interval, cutoffs):
    """Runs a simulation that considers congestion on single tracks and handles runner DNFs due to cutoffs."""
    print("Starting simulation with congestion model...")
    if cutoffs:
        print("Cutoff points enabled:")
        for dist, time in cutoffs:
            print(f"  - {dist} km at {time} hours")
    
    # --- Prepare runners ---
    runners_pace_sec_per_meter = np.random.normal(
        loc=avg_pace_min_per_km * 60 / 1000, 
        scale=std_dev_pace * 60 / 1000, 
        size=num_runners
    )
    
    # --- Configure wave start ---
    runner_start_times_sec = np.zeros(num_runners)
    if wave_groups > 1 and wave_interval > 0:
        print(f"Setting up a wave start with {wave_groups} waves at {wave_interval}-minute intervals.")
        runners_per_wave = int(np.ceil(num_runners / wave_groups))
        for i in range(num_runners):
            wave_index = i // runners_per_wave
            runner_start_times_sec[i] = wave_index * wave_interval * 60
    
    # --- Simulation settings ---
    time_step_sec = 10
    total_steps = time_limit_hours * 3600 // time_step_sec
    
    # --- Divide the course into small 'cells' ---
    cell_size_m = 10  # 10m intervals
    max_distance_m = course_df['distance'].iloc[-1]
    num_cells = int(np.ceil(max_distance_m / cell_size_m))
    
    cell_occupancy = np.zeros(num_cells, dtype=int)
    
    cell_capacity = np.zeros(num_cells, dtype=int)
    cell_gradient = np.zeros(num_cells, dtype=float)
    for i in range(num_cells):
        cell_start_m = i * cell_size_m
        point_in_cell = course_df.iloc[(course_df['distance'] - (cell_start_m + cell_size_m/2)).abs().argsort()[:1]]
        cell_capacity[i] = point_in_cell['capacity'].values[0]
        if 'gradient' in point_in_cell.columns:
            cell_gradient[i] = point_in_cell['gradient'].values[0]

    # --- For recording simulation data ---
    runner_positions = np.zeros((total_steps, num_runners))
    # Add a status tracker for DNF (Did Not Finish)
    runner_status = np.full(num_runners, 'active') # 'active' or 'dnf'
    
    # --- Simulation loop ---
    for t in range(1, total_steps):
        runner_positions[t] = runner_positions[t-1]
        current_time_sec = t * time_step_sec
        
        # --- Check for cutoffs, considering wave starts ---
        for cutoff_dist_km, cutoff_time_h in cutoffs:
            cutoff_time_sec = cutoff_time_h * 3600
            
            # Optimization: only check if the current time is past the first possible cutoff time
            if current_time_sec >= cutoff_time_sec:
                cutoff_dist_m = cutoff_dist_km * 1000
                
                # Calculate each runner's personal cutoff time in seconds
                # This is the base cutoff time plus their individual start delay
                personal_cutoff_times_sec = cutoff_time_sec + runner_start_times_sec
                
                # Find runners who are active, have passed their personal cutoff time, 
                # but have not reached the cutoff distance.
                dnf_indices = np.where(
                    (runner_status == 'active') &
                    (current_time_sec >= personal_cutoff_times_sec) &
                    (runner_positions[t] < cutoff_dist_m)
                )[0]
                
                if len(dnf_indices) > 0:
                    runner_status[dnf_indices] = 'dnf'
        
        cell_occupancy.fill(0)
        active_runner_indices = np.where(runner_status == 'active')[0]
        current_cells = (runner_positions[t, active_runner_indices] / cell_size_m).astype(int)
        np.add.at(cell_occupancy, current_cells[current_cells < num_cells], 1)

        sorted_runner_indices = np.argsort(runner_positions[t])[::-1]

        for r in sorted_runner_indices:
            # Skip runners who are DNF
            if runner_status[r] == 'dnf':
                continue
            
            # Skip runners who have not yet reached their start time
            if current_time_sec < runner_start_times_sec[r]:
                continue

            current_pos = runner_positions[t, r]
            if current_pos >= max_distance_m: continue

            # --- Pace Adjustment based on Gradient ---
            current_cell_idx = int(current_pos / cell_size_m)
            adjusted_pace_sec_per_meter = runners_pace_sec_per_meter[r]
            if current_cell_idx < num_cells:
                gradient = cell_gradient[current_cell_idx]
                # A simple model for pace adjustment:
                # - Uphill (positive gradient) slows the runner down (increases time per meter).
                # - Downhill (negative gradient) speeds them up (decreases time per meter).
                # The factors (0.02 for uphill, 0.01 for downhill) can be fine-tuned.
                if gradient > 0:
                    adjustment_factor = 1 + gradient * 0.02
                else:
                    adjustment_factor = 1 + gradient * 0.01  # gradient is negative, so this reduces the factor
                
                # Ensure the pace does not become zero or negative (infinitely fast)
                # We set a minimum adjustment factor to prevent this.
                adjustment_factor = max(0.2, adjustment_factor) # Limit max speed increase on downhills
                adjusted_pace_sec_per_meter *= adjustment_factor

            # Calculate the distance the runner would ideally move in this time step
            ideal_distance_moved = time_step_sec / adjusted_pace_sec_per_meter
            ideal_next_pos = current_pos + ideal_distance_moved
            
            ideal_next_cell_idx = int(ideal_next_pos / cell_size_m)
            
            allowed_pos = ideal_next_pos

            for cell_idx in range(current_cell_idx + 1, ideal_next_cell_idx + 1):
                if cell_idx >= num_cells: break
                
                if cell_occupancy[cell_idx] >= cell_capacity[cell_idx]:
                    allowed_pos = cell_idx * cell_size_m - 0.01
                    break
                else:
                    cell_occupancy[cell_idx] += 1
            
            runner_positions[t, r] = min(allowed_pos, max_distance_m)

    # --- Convert results to DataFrame ---
    results_df = pd.DataFrame(runner_positions, columns=[f'runner_{i+1}' for i in range(num_runners)])
    results_df['time_sec'] = np.arange(total_steps) * time_step_sec
    return results_df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run a trail running simulation using a JSON parameter file.'
    )
    parser.add_argument(
        'course_data_csv', 
        type=str, 
        help='Path to the course data CSV file (generated from GPX).'
    )
    parser.add_argument(
        'params_json',
        type=str,
        help='Path to the JSON file containing simulation parameters.'
    )
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        help='Path to the output CSV file. Overrides the one in the JSON file if provided.'
    )
    args = parser.parse_args()

    # --- Load parameters from JSON ---
    try:
        with open(args.params_json, 'r') as f:
            params = json.load(f)
    except FileNotFoundError:
        print(f"Error: Parameter file '{args.params_json}' not found.")
        exit()
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{args.params_json}'.")
        exit()

    # --- Extract parameters with defaults ---
    sim_params = params.get('simulation', {})
    
    settings = sim_params.get('settings', {})
    num_runners = settings.get('runners', 500)
    avg_pace = settings.get('avg_pace_min_per_km', 10.0)
    std_dev = settings.get('std_dev_pace', 1.5)
    time_limit = settings.get('time_limit_hours', 24)

    wave_settings = sim_params.get('wave_start', {})
    wave_groups = wave_settings.get('groups', 1)
    wave_interval = wave_settings.get('interval_minutes', 0)

    cutoffs_list = sim_params.get('cutoffs', [])
    cutoffs = [(c['distance_km'], c['time_hours']) for c in cutoffs_list]

    single_track_definitions = sim_params.get('single_track_sections', [])

    # --- Load course data ---
    try:
        course_data = pd.read_csv(args.course_data_csv)
    except FileNotFoundError:
        print(f"Error: Course data file '{args.course_data_csv}' not found.")
        exit()

    # --- Run simulation ---
    course_data_with_capacity = define_course_capacity(course_data, single_track_definitions)
    simulation_results = run_congestion_simulation(
        num_runners, avg_pace, std_dev, time_limit, course_data_with_capacity,
        wave_groups, wave_interval, cutoffs
    )
    
    # --- Save results ---
    output_filename = args.output if args.output else f'congestion_sim_results_{num_runners}runners.csv'
    
    simulation_results.to_csv(output_filename, index=False)
    print(f"\nSimulation complete. Results saved to '{output_filename}'.")
