import gpxpy
import pandas as pd
import numpy as np
import argparse
import os

def parse_gpx(file_path):
    """
    Parses a GPX file and returns the course information as a DataFrame.

    Args:
        file_path (str): Path to the GPX file.

    Returns:
        pandas.DataFrame: DataFrame containing the course information.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred while parsing the GPX file: {e}")
        return None

    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                # Get the distance from the 'distance' extension tag in the GPX file
                distance_extension = [ext for ext in point.extensions if 'distance' in ext.tag]
                distance = float(distance_extension[0].text) if distance_extension else 0
                points.append({
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                    'distance': distance # Cumulative distance from the start
                })

    if not points:
        print("Warning: No track points found in the GPX file.")
        return pd.DataFrame()

    df = pd.DataFrame(points)
    
    # Calculate the distance, elevation difference, and gradient for each segment
    df['segment_distance'] = df['distance'].diff().fillna(0)
    df['elevation_diff'] = df['elevation'].diff().fillna(0)
    
    # Avoid division by zero for segments with no distance
    df['gradient'] = np.where(df['segment_distance'] > 0, (df['elevation_diff'] / df['segment_distance']) * 100, 0)

    return df

def main(gpx_filepath):
    """
    Main process. Parses a GPX file and saves it as a CSV.
    """
    print(f"Parsing '{gpx_filepath}'...")
    course_df = parse_gpx(gpx_filepath)

    if course_df is not None and not course_df.empty:
        # Generate the output filename (e.g., my_race.gpx -> my_race_course_data.csv)
        base_filename = os.path.splitext(os.path.basename(gpx_filepath))[0]
        output_csv_path = f"{base_filename}_course_data.csv"
        
        # Save the results as a CSV file
        course_df.to_csv(output_csv_path, index=False)

        # Print the first few rows to confirm
        print("\nFirst 5 rows of the course data:")
        print(course_df.head())
        print(f"\nTotal course length: {course_df['distance'].iloc[-1] / 1000:.2f} km")
        print(f"Data has been saved to '{output_csv_path}'.")

if __name__ == '__main__':
    # Setup for parsing command-line arguments
    parser = argparse.ArgumentParser(
        description='Parse a GPX file and save its track data as a CSV file.'
    )
    # Add the GPX file path as a required argument
    parser.add_argument(
        'gpx_filepath', 
        type=str, 
        help='Path to the GPX file to be parsed.'
    )
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the main process
    main(args.gpx_filepath)

