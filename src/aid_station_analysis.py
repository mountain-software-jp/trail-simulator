import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import json

def analyze_aid_station_congestion(csv_filepath, aid_stations_km, output_filename):
    """
    Analyzes runner passage times at specified points from simulation results
    and visualizes congestion as a histogram.

    Args:
        csv_filepath (str): Path to the simulation result CSV file.
        aid_stations_km (list): List of aid station distances (km) to analyze.
        output_filename (str): The output image file name for the graph.
    """
    try:
        df = pd.read_csv(csv_filepath)
        print(f"Successfully loaded '{csv_filepath}'.")
    except FileNotFoundError:
        print(f"Error: File '{csv_filepath}' not found.")
        return

    # --- Get the total number of runners ---
    runner_columns = [col for col in df.columns if col.startswith('runner_')]
    num_runners = len(runner_columns)
    
    # --- Prepare for plotting ---
    plt.style.use('seaborn-v0_8-whitegrid')
    # Dynamically set the number of rows for the plot
    fig, axes = plt.subplots(len(aid_stations_km), 1, figsize=(14, 4 * len(aid_stations_km)), sharex=True)
    # Ensure axes is a list even if there is only one plot
    if len(aid_stations_km) == 1:
        axes = [axes]
    fig.suptitle(f'Aid Station Passage Time Distribution ({num_runners} Runners)', fontsize=20, fontweight='bold')

    # --- Calculate and plot passage times for each aid station ---
    for i, distance_km in enumerate(aid_stations_km):
        distance_m = distance_km * 1000
        passage_times_sec = []
        
        # Loop through runner columns (runner_1, runner_2, ...)
        for runner_col in runner_columns:
            # Get the data point where the runner first exceeds the specified distance
            passage_event = df[df[runner_col] >= distance_m]
            
            if not passage_event.empty:
                # Get the first passage time in seconds
                passage_time = passage_event['time_sec'].iloc[0]
                passage_times_sec.append(passage_time)
        
        if not passage_times_sec:
            print(f"No runners passed the {distance_km}km point.")
            # Hide the corresponding plot axis
            axes[i].axis('off')
            axes[i].text(0.5, 0.5, f'No runners passed {distance_km}km point.', 
                         ha='center', va='center', fontsize=12, style='italic')
            continue

        # Convert seconds to hours
        passage_times_hours = [t / 3600 for t in passage_times_sec]
        
        # Plot the histogram
        ax = axes[i]
        ax.hist(passage_times_hours, bins=50, color='teal', edgecolor='black', alpha=0.8)
        
        # Draw a line at the peak congestion time
        # Get the mode of the histogram (the position of the highest bar)
        counts, bin_edges = np.histogram(passage_times_hours, bins=50)
        peak_time_start = bin_edges[np.argmax(counts)]
        peak_time_end = bin_edges[np.argmax(counts) + 1]
        peak_time_center = (peak_time_start + peak_time_end) / 2
        
        ax.axvline(peak_time_center, color='magenta', linestyle='--', linewidth=2, label=f'Peak Time: ~{peak_time_center:.1f} h')

        ax.set_title(f'Congestion at {distance_km}km Point', fontsize=16)
        ax.set_ylabel('Number of Runners', fontsize=12)
        ax.legend()

    axes[-1].set_xlabel('Time Since Race Start (hours)', fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # --- Save the graph to an image file ---
    plt.savefig(output_filename)
    print(f"\nAnalysis complete.")
    print(f"The resulting graph has been saved as '{output_filename}'.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Analyze aid station congestion from a race simulation using a project JSON file.'
    )
    parser.add_argument(
        'csv_filepath', 
        type=str, 
        help='Path to the simulation result CSV file.'
    )
    parser.add_argument(
        'project_params_json',
        type=str,
        help='Path to the project JSON file containing all parameters.'
    )
    args = parser.parse_args()

    # --- Load parameters from JSON ---
    try:
        with open(args.project_params_json, 'r') as f:
            params = json.load(f)
    except FileNotFoundError:
        print(f"Error: Parameter file '{args.project_params_json}' not found.")
        exit()
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{args.project_params_json}'.")
        exit()

    # --- Extract parameters for this specific analysis ---
    analysis_params = params.get('analysis', {}).get('aid_station', {})
    stations_km = analysis_params.get('stations_km', [25, 50, 75, 95])
    output_filename = analysis_params.get('output_filename', 'aid_station_congestion.png')
    
    analyze_aid_station_congestion(args.csv_filepath, stations_km, output_filename)
