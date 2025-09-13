import pandas as pd
import numpy as np
import argparse

def define_course_capacity(course_df, single_track_sections):
    """Adds a 'capacity' column to the course data DataFrame."""
    # Default is a wide road (large capacity)
    course_df['capacity'] = 1000 
    
    for section in single_track_sections:
        start_km, end_km, capacity = section['range_km'][0], section['range_km'][1], section['capacity']
        start_m, end_m = start_km * 1000, end_km * 1000
        # Set the capacity for the specified section
        course_df.loc[(course_df['distance'] >= start_m) & (course_df['distance'] <= end_m), 'capacity'] = capacity
        print(f"Set course from {start_km}km to {end_km}km as a single track with capacity {capacity}.")
    return course_df

def run_congestion_simulation(num_runners, avg_pace_min_per_km, std_dev_pace, time_limit_hours, course_df):
    """
    [Congestion Model Ver.] Runs a simulation that considers single-track congestion.
    """
    print("Starting simulation with the congestion model...")
    
    # --- Runner Preparation ---
    runners_pace_sec_per_meter = np.random.normal(
        loc=avg_pace_min_per_km * 60 / 1000, 
        scale=std_dev_pace * 60 / 1000, 
        size=num_runners
    )
    
    # --- Simulation Settings ---
    time_step_sec = 10
    total_steps = time_limit_hours * 3600 // time_step_sec
    
    # --- Divide the course into small "cells" ---
    cell_size_m = 10  # Divide into 10m segments
    max_distance_m = course_df['distance'].iloc[-1]
    num_cells = int(np.ceil(max_distance_m / cell_size_m))
    
    # Current number of runners in each cell
    cell_occupancy = np.zeros(num_cells, dtype=int)
    
    # Maximum number of runners in each cell (capacity)
    cell_capacity = np.zeros(num_cells, dtype=int)
    for i in range(num_cells):
        cell_start_m = i * cell_size_m
        # Use the capacity from the midpoint of the cell as representative
        point_in_cell = course_df.iloc[(course_df['distance'] - (cell_start_m + cell_size_m/2)).abs().argsort()[:1]]
        cell_capacity[i] = point_in_cell['capacity'].values[0]

    # --- For recording simulation data ---
    runner_positions = np.zeros((total_steps, num_runners))
    
    # --- Simulation Loop ---
    for t in range(1, total_steps):
        runner_positions[t] = runner_positions[t-1]
        
        # Reset cell occupancy
        cell_occupancy.fill(0)
        # Update cell occupancy based on the current positions of all runners
        current_cells = (runner_positions[t] / cell_size_m).astype(int)
        np.add.at(cell_occupancy, current_cells[current_cells < num_cells], 1)

        # Process runners sorted by speed (faster runners get priority)
        sorted_runner_indices = np.argsort(runner_positions[t])[::-1]

        for r in sorted_runner_indices:
            current_pos = runner_positions[t, r]
            if current_pos >= max_distance_m: continue # Already finished

            # 1. Calculate the ideal distance to move based on original pace
            # ... (Pace adjustment due to gradient is omitted here for simplicity)
            ideal_distance_moved = time_step_sec / runners_pace_sec_per_meter[r]
            ideal_next_pos = current_pos + ideal_distance_moved

            # 2. Check if the next cell is available
            current_cell_idx = int(current_pos / cell_size_m)
            ideal_next_cell_idx = int(ideal_next_pos / cell_size_m)
            
            allowed_pos = ideal_next_pos

            # If crossing into a new cell, check the capacity of subsequent cells
            for cell_idx in range(current_cell_idx + 1, ideal_next_cell_idx + 1):
                if cell_idx >= num_cells: break
                
                if cell_occupancy[cell_idx] >= cell_capacity[cell_idx]:
                    # If capacity is exceeded, can only move to the edge of that cell
                    allowed_pos = cell_idx * cell_size_m - 0.01 # Just before the cell boundary
                    break
                else:
                    # If able to proceed, increment the occupancy of that cell
                    cell_occupancy[cell_idx] += 1
            
            # 3. Update the final position
            runner_positions[t, r] = min(allowed_pos, max_distance_m)

    # --- Convert results to a DataFrame ---
    results_df = pd.DataFrame(runner_positions, columns=[f'runner_{i+1}' for i in range(num_runners)])
    results_df['time_sec'] = np.arange(total_steps) * time_step_sec
    return results_df


if __name__ == '__main__':
    # --- Command-line Argument Setup ---
    parser = argparse.ArgumentParser(description='Run a trail running simulation with a congestion model.')
    parser.add_argument('course_data_csv', type=str, help='Path to the course data CSV file (generated from GPX).')
    # --- Add simulation parameters as arguments ---
    parser.add_argument('-n', '--runners', type=int, default=500, help='Number of runners. Default: 500')
    parser.add_argument('-p', '--avg_pace', type=float, default=10.0, help='Average pace in minutes per km. Default: 10.0')
    parser.add_argument('-s', '--std_dev', type=float, default=1.5, help='Standard deviation of pace. Default: 1.5')
    parser.add_argument('-t', '--time_limit', type=int, default=24, help='Time limit in hours. Default: 24')

    args = parser.parse_args()

    # --- Single Track Section Definitions ---
    # Please define these sections freely according to the actual race course.
    single_track_definitions = [
        {'range_km': (5, 8), 'capacity': 2},    # From 5km to 8km, capacity is 2
        {'range_km': (20, 22.5), 'capacity': 1}, # From 20km to 22.5km, a very narrow section with capacity 1
    ]

    # --- Execution ---
    # 1. Load course data from CSV (using the file specified as an argument)
    try:
        course_data = pd.read_csv(args.course_data_csv)
    except FileNotFoundError:
        print(f"Error: File '{args.course_data_csv}' not found.")
        exit()

    # 2. Add capacity information to the course data
    course_data_with_capacity = define_course_capacity(course_data, single_track_definitions)
    # 3. Run the simulation with the congestion model
    simulation_results = run_congestion_simulation(
        args.runners, args.avg_pace, args.std_dev, args.time_limit, course_data_with_capacity
    )
    # 4. Save the results
    output_filename = f'congestion_sim_results_{args.runners}runners.csv'
    simulation_results.to_csv(output_filename, index=False)
    print(f"\nSimulation complete. Results saved to '{output_filename}'.")

