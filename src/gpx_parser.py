import gpxpy
import pandas as pd
import numpy as np
import argparse
import os
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two points on Earth using the Haversine formula.
    """
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) * math.sin(delta_phi / 2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def parse_gpx(file_path):
    """
    Parses a GPX file and returns the course information as a DataFrame.
    It handles GPX files with or without the <distance> extension.
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
    cumulative_distance = 0.0
    previous_point = None

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                # First, try to get distance from the extension tag
                distance_extension = [ext for ext in point.extensions if 'distance' in ext.tag]
                
                if distance_extension:
                    # Use the pre-calculated distance if available
                    distance = float(distance_extension[0].text)
                else:
                    # If not available, calculate it from lat/lon
                    if previous_point:
                        segment_dist = haversine_distance(
                            previous_point.latitude, previous_point.longitude,
                            point.latitude, point.longitude
                        )
                        cumulative_distance += segment_dist
                    distance = cumulative_distance
                
                points.append({
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                    'distance': distance 
                })
                previous_point = point

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

def main(gpx_filepath, output_filepath=None):
    """
    Main process. Parses a GPX file and saves it as a CSV.
    """
    print(f"Parsing '{gpx_filepath}'...")
    course_df = parse_gpx(gpx_filepath)

    if course_df is not None and not course_df.empty:
        # Generate the output filename if not provided
        if output_filepath:
            output_csv_path = output_filepath
        else:
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
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Path to the output CSV file. If not provided, a default name will be generated.'
    )
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the main process
    main(args.gpx_filepath, args.output)
