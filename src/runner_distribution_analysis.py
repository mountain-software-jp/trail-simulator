import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse

def analyze_snapshot(simulation_csv, course_data_csv, snapshot_times_hours):
    """
    Reads a simulation result CSV, visualizes the runner distribution at specific times
    as a histogram, and displays the course elevation profile.
    Finished runners are excluded from the distribution calculation.

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
        finish_line_m = df_course['distance'].iloc[-1]
        print(f"Set total course length to {finish_line_m / 1000:.2f} km.")
    except FileNotFoundError:
        print(f"Error: File '{course_data_csv}' not found.")
        return

    # --- Plot Layout Setup ---
    num_snapshots = len(snapshot_times_hours)
    # Add 1 plot for the elevation profile
    num_plots = num_snapshots + 1
    
    plt.style.use('seaborn-v0_8-whitegrid')
    # Create height ratios: histograms are 3 times taller than the elevation profile
    height_ratios = [3] * num_snapshots + [1]
    
    fig, axes = plt.subplots(
        num_plots, 1, 
        figsize=(16, 5 * num_snapshots + 3), 
        sharex=True, 
        gridspec_kw={'height_ratios': height_ratios}
    )
    
    # If there's only one snapshot, axes is not a list. Make it a list.
    if num_snapshots == 0:
        # Handle case with no snapshots, just show elevation
        fig, axes = plt.subplots(1,1, figsize=(16,5))
        axes = [axes]
    elif num_plots == 2: # 1 snapshot + 1 elevation
        axes = list(axes)

    num_runners = len([col for col in df_sim.columns if col.startswith('runner_')])
    fig.suptitle(f'Snapshot of Active Runner Distribution ({num_runners} Total Runners)', fontsize=20, fontweight='bold')

    # --- Plot Runner Distribution Snapshots ---
    for i, time_h in enumerate(snapshot_times_hours):
        time_sec = time_h * 3600
        closest_time_index = (df_sim['time_sec'] - time_sec).abs().idxmin()
        snapshot_row = df_sim.loc[[closest_time_index]]
        
        if snapshot_row.empty:
            print(f"Data for {time_h} hours could not be found.")
            continue
            
        runner_positions = snapshot_row.drop(columns='time_sec').values.flatten()
        
        active_runner_positions = runner_positions[runner_positions < finish_line_m]
        num_finishers = len(runner_positions) - len(active_runner_positions)
        active_runner_positions_km = active_runner_positions / 1000
        
        ax = axes[i]
        ax.hist(active_runner_positions_km, bins=80, color='skyblue', edgecolor='black', alpha=0.8, range=(0, finish_line_m/1000))
        
        mean_pos = np.mean(active_runner_positions_km) if len(active_runner_positions_km) > 0 else 0
        ax.axvline(mean_pos, color='red', linestyle='--', linewidth=2, label=f'Average (Active): {mean_pos:.1f} km')
        
        ax.text(0.98, 0.95, f'Finishers: {num_finishers}',
                transform=ax.transAxes, fontsize=12,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.5', fc='gold', alpha=0.7))
        
        ax.set_title(f'Distribution After {time_h} Hours (Active Runners Only)', fontsize=16)
        ax.set_ylabel('Number of Runners', fontsize=12)
        ax.legend()
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # --- Plot Course Elevation Profile ---
    ax_elevation = axes[-1]
    course_dist_km = df_course['distance'] / 1000
    course_elev_m = df_course['elevation']
    
    ax_elevation.plot(course_dist_km, course_elev_m, color='darkgreen', linewidth=1.5)
    ax_elevation.fill_between(course_dist_km, course_elev_m, alpha=0.2, color='darkgreen')
    ax_elevation.set_title('Course Elevation Profile', fontsize=14)
    ax_elevation.set_ylabel('Elevation (m)', fontsize=12)
    ax_elevation.set_xlabel('Distance from Start (km)', fontsize=12)
    ax_elevation.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax_elevation.set_xlim(0, finish_line_m / 1000)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_filename = f'runner_distribution_snapshot_{num_runners}runners_active.png'
    plt.savefig(output_filename)
    print(f"\nAnalysis complete.")
    print(f"The resulting graph has been saved as '{output_filename}'.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Analyze active runner distribution from a race simulation CSV file and plot it against the course elevation profile.'
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

