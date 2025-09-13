import pandas as pd
import numpy as np
import argparse

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

def run_congestion_simulation(num_runners, avg_pace_min_per_km, std_dev_pace, time_limit_hours, course_df, wave_groups, wave_interval):
    """Runs a simulation that considers congestion on single tracks (Congestion Model Ver.)."""
    print("Starting simulation with congestion model...")
    
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
    for i in range(num_cells):
        cell_start_m = i * cell_size_m
        point_in_cell = course_df.iloc[(course_df['distance'] - (cell_start_m + cell_size_m/2)).abs().argsort()[:1]]
        cell_capacity[i] = point_in_cell['capacity'].values[0]

    # --- For recording simulation data ---
    runner_positions = np.zeros((total_steps, num_runners))
    
    # --- Simulation loop ---
    for t in range(1, total_steps):
        runner_positions[t] = runner_positions[t-1]
        
        cell_occupancy.fill(0)
        current_cells = (runner_positions[t] / cell_size_m).astype(int)
        np.add.at(cell_occupancy, current_cells[current_cells < num_cells], 1)

        sorted_runner_indices = np.argsort(runner_positions[t])[::-1]

        for r in sorted_runner_indices:
            current_time_sec = t * time_step_sec
            # Skip runners who have not yet reached their start time
            if current_time_sec < runner_start_times_sec[r]:
                continue

            current_pos = runner_positions[t, r]
            if current_pos >= max_distance_m: continue

            ideal_distance_moved = time_step_sec / runners_pace_sec_per_meter[r]
            ideal_next_pos = current_pos + ideal_distance_moved

            current_cell_idx = int(current_pos / cell_size_m)
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
    parser = argparse.ArgumentParser(description='Run a trail running simulation with a congestion model.')
    parser.add_argument('course_data_csv', type=str, help='Path to the course data CSV file (generated from GPX)')
    parser.add_argument('-n', '--runners', type=int, default=500, help='Number of runners (default: 500)')
    parser.add_argument('-p', '--avg_pace', type=float, default=10.0, help='Overall average pace in minutes/km (default: 10.0)')
    parser.add_argument('-s', '--std_dev', type=float, default=1.5, help='Standard deviation of pace (default: 1.5)')
    parser.add_argument('-t', '--time_limit', type=int, default=24, help='Race time limit in hours (default: 24)')
    # --- Add arguments for wave start ---
    parser.add_argument('--wave_groups', type=int, default=1, help='Number of groups for wave start (default: 1, for a mass start)')
    parser.add_argument('--wave_interval', type=int, default=0, help='Start interval between waves in minutes (default: 0)')

    args = parser.parse_args()

    # --- Definition of single track sections ---
    # Customize these definitions to match your actual race course
    single_track_definitions = [
        {'range_km': (5, 8), 'capacity': 2},    # From 5km to 8km, capacity is 2 runners
        {'range_km': (20, 22.5), 'capacity': 1}, # From 20km to 22.5km, capacity is 1 runner
    ]

    try:
        course_data = pd.read_csv(args.course_data_csv)
    except FileNotFoundError:
        print(f"Error: File '{args.course_data_csv}' not found.")
        exit()

    course_data_with_capacity = define_course_capacity(course_data, single_track_definitions)
    simulation_results = run_congestion_simulation(
        args.runners, args.avg_pace, args.std_dev, args.time_limit, course_data_with_capacity,
        args.wave_groups, args.wave_interval
    )
    
    output_filename = f'congestion_sim_results_{args.runners}runners.csv'
    simulation_results.to_csv(output_filename, index=False)
    print(f"\nSimulation complete. Results saved to '{output_filename}'.")

