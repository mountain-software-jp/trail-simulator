import pandas as pd
import numpy as np
import argparse
import json
import os

def create_standalone_animation(simulation_csv, course_csv, output_html, time_step_min, max_runners_to_display):
    """
    Generates a standalone HTML animation map that plots runners as moving dots
    based on the simulation data.

    Args:
        simulation_csv (str): Path to the simulation results CSV file.
        course_csv (str): Path to the course data CSV file (containing distance, lat, lon).
        output_html (str): The name of the output HTML file.
        time_step_min (int): The time interval in minutes for generating animation frames.
        max_runners_to_display (int): The maximum number of runners to display on the map.
    """
    print("Loading data...")
    try:
        sim_df = pd.read_csv(simulation_csv)
        course_df = pd.read_csv(course_csv)
    except FileNotFoundError as e:
        print(f"Error: {e}. Please check your file paths.")
        return

    print("Processing data...")
    
    runner_cols_all = [col for col in sim_df.columns if col.startswith('runner_')]
    
    if len(runner_cols_all) > max_runners_to_display:
        print(f"Displaying a random sample of {max_runners_to_display} out of {len(runner_cols_all)} runners for performance.")
        runner_cols = np.random.choice(runner_cols_all, max_runners_to_display, replace=False).tolist()
    else:
        runner_cols = runner_cols_all

    time_col = 'time_sec'
    sim_long_df = sim_df.melt(id_vars=[time_col], value_vars=runner_cols, var_name='runner', value_name='distance')

    time_step_sec = time_step_min * 60
    # Ensure the first time step (0) is always included
    time_mask = (sim_long_df['time_sec'] % time_step_sec == 0) | (sim_long_df['time_sec'] == 0)
    sim_long_df = sim_long_df[time_mask].copy()

    print("Mapping runner distances to geographic coordinates with interpolation...")
    course_distances = course_df['distance'].values
    course_latitudes = course_df['latitude'].values
    course_longitudes = course_df['longitude'].values
    finish_line_m = course_distances[-1]
    
    # Exclude runners who have finished for efficiency before interpolation
    sim_long_df = sim_long_df[sim_long_df['distance'] < finish_line_m]

    distances_to_map = sim_long_df['distance'].values
    start_indices = np.searchsorted(course_distances, distances_to_map, side='right') - 1
    start_indices = np.clip(start_indices, 0, len(course_distances) - 2)
    end_indices = start_indices + 1

    lat1, lon1, dist1 = course_latitudes[start_indices], course_longitudes[start_indices], course_distances[start_indices]
    lat2, lon2, dist2 = course_latitudes[end_indices], course_longitudes[end_indices], course_distances[end_indices]

    segment_length = dist2 - dist1
    ratio = np.zeros_like(distances_to_map, dtype=float)
    non_zero_len_mask = segment_length > 0
    ratio[non_zero_len_mask] = (distances_to_map[non_zero_len_mask] - dist1[non_zero_len_mask]) / segment_length[non_zero_len_mask]
    
    sim_long_df['latitude'] = lat1 + (lat2 - lat1) * ratio
    sim_long_df['longitude'] = lon1 + (lon2 - lon1) * ratio
    
    print("Preparing animation data for HTML...")
    animation_data = {}
    time_indices = sorted(sim_long_df['time_sec'].unique())

    for t in time_indices:
        # Convert numpy.int64 to standard Python int for JSON compatibility
        time_key = int(t)
        locations = sim_long_df[sim_long_df['time_sec'] == t][['latitude', 'longitude']].values.tolist()
        animation_data[time_key] = locations
    
    course_path_json = json.dumps(course_df[['latitude', 'longitude']].values.tolist())
    map_center_json = json.dumps([course_df['latitude'].mean(), course_df['longitude'].mean()])

    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Race Animation</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ height: 100vh; width: 100%; }}
        .controls {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            z-index: 1000;
            display: flex;
            align-items: center;
        }}
        .controls input[type=range] {{
            width: 400px;
            margin: 0 10px;
        }}
        .controls button, .controls label {{
            margin: 0 5px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="controls">
        <button id="playPauseBtn">Play</button>
        <label id="timeLabel">00:00:00</label>
        <input type="range" id="timeSlider" min="0" value="0">
    </div>

    <script>
        const animationData = {json.dumps(animation_data)};
        const coursePath = {course_path_json};
        const mapCenter = {map_center_json};
        
        const map = L.map('map').setView(mapCenter, 12);
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        }}).addTo(map);

        L.polyline(coursePath, {{ color: 'gray', weight: 3, opacity: 0.8 }}).addTo(map);

        const timeSlider = document.getElementById('timeSlider');
        const timeLabel = document.getElementById('timeLabel');
        const playPauseBtn = document.getElementById('playPauseBtn');

        const timeSteps = Object.keys(animationData).map(Number).sort((a, b) => a - b);
        timeSlider.max = timeSteps.length - 1;

        let runnerLayer = L.layerGroup().addTo(map);
        let animationInterval = null;

        function formatTime(seconds) {{
            const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
            const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
            const s = (seconds % 60).toString().padStart(2, '0');
            return `${{h}}:${{m}}:${{s}}`;
        }}

        function updateMap(sliderValue) {{
            const timeKey = timeSteps[sliderValue];
            timeLabel.textContent = formatTime(timeKey);
            
            runnerLayer.clearLayers();
            
            const locations = animationData[timeKey] || [];
            locations.forEach(loc => {{
                L.circleMarker([loc[0], loc[1]], {{
                    radius: 3,
                    fillColor: "#0078A8",
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }}).addTo(runnerLayer);
            }});
        }}

        timeSlider.addEventListener('input', (e) => {{
            updateMap(parseInt(e.target.value, 10));
        }});

        playPauseBtn.addEventListener('click', () => {{
            if (animationInterval) {{
                clearInterval(animationInterval);
                animationInterval = null;
                playPauseBtn.textContent = 'Play';
            }} else {{
                playPauseBtn.textContent = 'Pause';
                animationInterval = setInterval(() => {{
                    let currentValue = parseInt(timeSlider.value, 10);
                    if (currentValue < timeSlider.max) {{
                        currentValue++;
                        timeSlider.value = currentValue;
                        updateMap(currentValue);
                    }} else {{
                        clearInterval(animationInterval);
                        animationInterval = null;
                        playPauseBtn.textContent = 'Play';
                    }}
                }}, 200); // Animation speed (milliseconds)
            }}
        }});

        // Initial display
        updateMap(0);

    </script>
</body>
</html>
"""
    print(f"Saving standalone animation map to '{output_html}'...")
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a standalone dot animation map from race simulation data using a project JSON file.')
    parser.add_argument('simulation_csv', type=str, help='Path to the simulation results CSV file.')
    parser.add_argument('course_csv', type=str, help='Path to the course data CSV file (with lat/lon).')
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
    analysis_params = params.get('analysis', {}).get('dot_animation', {})
    output_filename = analysis_params.get('output_filename', 'dot_animation.html')
    time_step_min = analysis_params.get('time_step_minutes', 10)
    max_runners = analysis_params.get('max_runners_to_display', 300)

    create_standalone_animation(args.simulation_csv, args.course_csv, output_filename, time_step_min, max_runners)
