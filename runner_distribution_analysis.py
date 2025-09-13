import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse # Added to handle command-line arguments

def analyze_snapshot(simulation_csv, course_data_csv, snapshot_times_hours):
    """
    Reads a simulation result CSV, visualizes the runner distribution at specific times
    as a histogram, and excludes finished runners from the distribution calculation.

    Args:
        simulation_csv (str): Path to the simulation result CSV file.
        course_data_csv (str): Path to the course data CSV file (generated from GPX).
        snapshot_times_hours (list): A list of times (in hours) to take snapshots.
    """
    try:
        df_sim = pd.read_csv(simulation_csv)
        print(f"Successfully loaded '{simulation_csv}'.")
    except FileNotFoundError:
        print(f"Error: File '{simulation_csv}' not found.")
        return

    try:
        df_course = pd.read_csv(course_data_csv)
        # Get the final distance of the course (finish line)
        finish_line_m = df_course['distance'].iloc[-1]
        print(f"Set total course length to {finish_line_m / 1000:.2f} km.")
    except FileNotFoundError:
        print(f"Error: File '{course_data_csv}' not found.")
        return

    # --- Prepare for plotting ---
    num_plots = len(snapshot_times_hours)
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(num_plots, 1, figsize=(14, 5 * num_plots), sharex=True)
    if num_plots == 1:
        axes = [axes]

    num_runners = len([col for col in df_sim.columns if col.startswith('runner_')])
    fig.suptitle(f'Snapshot of Active Runner Distribution ({num_runners} Total Runners)', fontsize=20, fontweight='bold')


    for i, time_h in enumerate(snapshot_times_hours):
        time_sec = time_h * 3600
        closest_time_index = (df_sim['time_sec'] - time_sec).abs().idxmin()
        snapshot_row = df_sim.loc[[closest_time_index]]
        
        if snapshot_row.empty:
            print(f"Data for {time_h} hours could not be found.")
            continue
            
        runner_positions = snapshot_row.drop(columns='time_sec').values.flatten()
        
        # --- Exclude finished runners here ---
        active_runner_positions = runner_positions[runner_positions < finish_line_m]
        num_finishers = len(runner_positions) - len(active_runner_positions)
        
        active_runner_positions_km = active_runner_positions / 1000
        
        # --- Plotting the histogram ---
        ax = axes[i]
        ax.hist(active_runner_positions_km, bins=60, color='skyblue', edgecolor='black', alpha=0.8, range=(0, finish_line_m/1000))
        
        mean_pos = np.mean(active_runner_positions_km) if len(active_runner_positions_km) > 0 else 0
        ax.axvline(mean_pos, color='red', linestyle='--', linewidth=2, label=f'Average (Active): {mean_pos:.1f} km')
        
        # --- Display the number of finishers on the graph ---
        ax.text(0.98, 0.95, f'Finishers: {num_finishers}',
                transform=ax.transAxes, fontsize=12,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.5', fc='gold', alpha=0.7))
        
        ax.set_title(f'Distribution After {time_h} Hours (Active Runners Only)', fontsize=16)
        ax.set_ylabel('Number of Runners', fontsize=12)
        ax.legend()
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    axes[-1].set_xlabel('Distance from Start (km)', fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_filename = f'runner_distribution_snapshot_{num_runners}runners_active.png'
    plt.savefig(output_filename)
    print(f"\nAnalysis complete.")
    print(f"The resulting graph has been saved as '{output_filename}'.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Analyze active runner distribution from a race simulation CSV file.'
    )
    parser.add_argument(
        'simulation_csv', 
        type=str, 
        help='Path to the simulation result CSV file.'
    )
    parser.add_argument(
        'course_data_csv', 
        type=str, 
        help='Path to the course data CSV file (generated from GPX).'
    )
    parser.add_argument(
        '-t', '--times',
        nargs='+',
        type=float,
        default=[3, 10],
        help='A list of snapshot times in hours (e.g., -t 2.5 5 12).'
    )
    
    args = parser.parse_args()
    
    analyze_snapshot(args.simulation_csv, args.course_data_csv, args.times)

