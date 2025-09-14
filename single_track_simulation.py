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
    parser.add_argument('-o', '--output', type=str, help='Path to the output CSV file')
    parser.add_argument('-n', '--runners', type=int, default=500, help='Number of runners (default: 500)')
    parser.add_argument('-p', '--avg_pace', type=float, default=10.0, help='Overall average pace in minutes/km (default: 10.0)')
    parser.add_argument('-s', '--std_dev', type=float, default=1.5, help='Standard deviation of pace (default: 1.5)')
    parser.add_argument('-t', '--time_limit', type=int, default=24, help='Race time limit in hours (default: 24)')
    
    # --- Arguments for wave start ---
    parser.add_argument('--wave_groups', type=int, default=1, help='Number of groups for wave start (default: 1, for a mass start)')
    parser.add_argument('--wave_interval', type=int, default=0, help='Start interval between waves in minutes (default: 0)')

    # --- Arguments for single track definition ---
    st_group = parser.add_mutually_exclusive_group()
    st_group.add_argument('--single_track_config', type=str, help='Path to a JSON file defining single track sections.')
    st_group.add_argument('--simple_single_track', nargs=3, action='append', metavar=('START_PERC', 'END_PERC', 'CAPACITY'),
                          help='Define a single track section by course percentage. Can be used multiple times. E.g., --simple_single_track 10 20 2')
    st_group.add_argument('--random_single_track_percentage', nargs=2, metavar=('PERCENTAGE', 'CAPACITY'),
                          help='Define single track sections randomly based on a total percentage of the course. E.g., 5 1 for 5%% with capacity 1.')

    args = parser.parse_args()

    # --- Load course data ---
    try:
        course_data = pd.read_csv(args.course_data_csv)
    except FileNotFoundError:
        print(f"Error: File '{args.course_data_csv}' not found.")
        exit()

    # --- Determine single track definitions ---
    single_track_definitions = []
    if args.simple_single_track:
        print("Defining single tracks based on course percentage...")
        total_distance_km = course_data['distance'].iloc[-1] / 1000
        for start_perc, end_perc, capacity in args.simple_single_track:
            start_km = total_distance_km * (float(start_perc) / 100)
            end_km = total_distance_km * (float(end_perc) / 100)
            single_track_definitions.append({
                'range_km': (start_km, end_km),
                'capacity': int(capacity)
            })
            print(f"  - Added single track with capacity {capacity} from {start_km:.2f}km ({start_perc}%) to {end_km:.2f}km ({end_perc}%).")

    elif args.random_single_track_percentage:
        print("Defining single tracks randomly based on percentage...")
        percentage = float(args.random_single_track_percentage[0])
        capacity = int(args.random_single_track_percentage[1])
        total_distance_m = course_data['distance'].iloc[-1]
        
        # Using 100m chunks to randomly distribute single tracks
        chunk_size_m = 100
        num_chunks = int(np.ceil(total_distance_m / chunk_size_m))
        num_single_track_chunks = int(num_chunks * (percentage / 100))

        print(f"  - Total course length: {total_distance_m / 1000:.2f} km")
        print(f"  - Target single track percentage: {percentage}%")
        print(f"  - Total single track length: {num_single_track_chunks * chunk_size_m / 1000:.2f} km")
        print(f"  - Capacity for random single tracks: {capacity}")

        # Randomly select chunks to be single track
        single_track_indices = np.random.choice(num_chunks, num_single_track_chunks, replace=False)
        single_track_indices.sort()

        if len(single_track_indices) > 0:
            # Merge consecutive chunks into single track sections
            start_chunk = single_track_indices[0]
            end_chunk = single_track_indices[0]
            for i in range(1, len(single_track_indices)):
                if single_track_indices[i] == end_chunk + 1:
                    end_chunk = single_track_indices[i]
                else:
                    # End of a section, save it
                    start_km = (start_chunk * chunk_size_m) / 1000
                    end_km = ((end_chunk + 1) * chunk_size_m) / 1000
                    single_track_definitions.append({'range_km': (start_km, end_km), 'capacity': capacity})
                    print(f"  - Added random single track from {start_km:.2f}km to {end_km:.2f}km")
                    # Start of a new section
                    start_chunk = single_track_indices[i]
                    end_chunk = single_track_indices[i]
            
            # Add the very last section
            start_km = (start_chunk * chunk_size_m) / 1000
            end_km = ((end_chunk + 1) * chunk_size_m) / 1000
            single_track_definitions.append({'range_km': (start_km, end_km), 'capacity': capacity})
            print(f"  - Added random single track from {start_km:.2f}km to {end_km:.2f}km")

    elif args.single_track_config:
        print(f"Loading single track definitions from '{args.single_track_config}'...")
        try:
            with open(args.single_track_config, 'r') as f:
                single_track_definitions = json.load(f)
        except FileNotFoundError:
            print(f"Error: Single track config file '{args.single_track_config}' not found.")
            exit()
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{args.single_track_config}'.")
            exit()

    # --- Run simulation ---
    course_data_with_capacity = define_course_capacity(course_data, single_track_definitions)
    simulation_results = run_congestion_simulation(
        args.runners, args.avg_pace, args.std_dev, args.time_limit, course_data_with_capacity,
        args.wave_groups, args.wave_interval
    )
    
    # --- Save results ---
    if args.output:
        output_filename = args.output
    else:
        output_filename = f'congestion_sim_results_{args.runners}runners.csv'
    
    simulation_results.to_csv(output_filename, index=False)
    print(f"\nSimulation complete. Results saved to '{output_filename}'.")
