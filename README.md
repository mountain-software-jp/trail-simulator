# **Trail Running Race Congestion Simulator**

[Japanese/日本語](README_JA.md)

## **Overview**

This project provides a suite of Python scripts to simulate and analyze runner congestion in trail running races using GPX course data and the Monte Carlo method.

A key feature is its ability to model congestion on narrow single-track sections where overtaking is difficult, aiming for more realistic predictions. The primary goal is to assist race directors and organizers in making informed decisions by evaluating how factors like participant numbers and start times might affect the race, and by helping to plan resource allocation for aid stations.

### Samples

#### The grpah of the runner distribution snapshot 

![](sample/runner_distribution_snapshot_500runners_active.png)

#### The grpah of the aid station congestion

![](sample/aid_station_congestion.png)

## **Disclaimer**

This simulator is based on simplified physical models and statistical assumptions. Therefore, the simulation results should be considered as **approximations** and are not intended to be a perfect or exact representation of real-world race conditions.

Many unpredictable factors not modeled in this simulation can affect an actual race, including weather, trail conditions, individual runner's physical condition, equipment issues, and DNFs. The creator of this tool assumes no responsibility for any damages or losses resulting from its use.

## **Key Features**

* Extracts course information (distance, elevation, gradient) from GPX files.  
* Implements a Monte Carlo simulation where each runner's pace is based on a normal distribution.  
* Features a congestion model based on course capacity (e.g., for single tracks).  
* Visualizes the overall runner distribution at specific times with "Snapshot Analysis".  
* Analyzes passage times at specific points (e.g., aid stations) to visualize congestion peaks with "Checkpoint Analysis".

## **Setup**

### **Prerequisites**

To run these scripts, you will need the following Python libraries:

* gpxpy  
* pandas  
* numpy  
* matplotlib

You can install them all with a single command:

```shell
pip install gpxpy pandas numpy matplotlib
```

## **How to Use**

The workflow consists of four main steps, using the scripts in sequence:

[GPX File] -> (1. gpx_parser.py) -> [Course CSV] -> (2. single_track_simulation.py) -> [Simulation Result CSV] -> (3. & 4. Analysis Scripts) -> [Analysis Graphs]

### **Step 1: Create Course Data CSV from a GPX File**

First, convert your race's GPX file into a CSV format that the other scripts can read.

**Command**

```shell
python src/gpx_parser.py [path/to/your/gpx_file.gpx]
```

**Example**

```shell
python src/gpx_parser.py your_race.gpx

# Output  
A file named your_race_course_data.csv will be created.
```

### **Step 2: Run the Congestion Simulation**

Next, use the course data CSV from Step 1 to run the main simulation.

**Command**

```shell
python src/single_track_simulation.py [course_data.csv] [options]
```

**Options**

*   `-n, --runners`: Number of runners (Default: 500)
*   `-p, --avg_pace`: Average pace in minutes per km (Default: 10.0)
*   `-s, --std_dev`: Standard deviation of pace (Default: 1.5)
*   `-t, --time_limit`: Race time limit in hours (Default: 24)
*   `--wave_groups`: Number of groups for wave start (default: 1, for a mass start)
*   `--wave_interval`: Start interval between waves in minutes (default: 0)

**Single Track Definition Options**

You can define single-track sections using one of the following command-line options. These options are mutually exclusive.

*   `--single_track_config [JSON_FILE_PATH]`:
    Specify a JSON file that defines the single-track sections. This is the recommended way for complex courses. The JSON file should look like this:
    ```json
    [
        {"range_km": [5, 8], "capacity": 2},
        {"range_km": [20, 22.5], "capacity": 1}
    ]
    ```

*   `--simple_single_track [START_PERC] [END_PERC] [CAPACITY]`:
    Define a single-track section based on the percentage of the total course distance. This option can be used multiple times.
    *Example: To define a section with capacity 2 from 10% to 20% of the course:*
    ```shell
    --simple_single_track 10 20 2
    ```

*   `--random_single_track_percentage [PERCENTAGE] [CAPACITY]`:
    Randomly designate a certain percentage of the course as single-track with a given capacity.
    *Example: To make 5% of the course a single-track with capacity 1:*
    ```shell
    --random_single_track_percentage 5 1
    ```

**Example (Simulating a race with 1500 runners and defining single tracks via a JSON file)**

```shell
python src/single_track_simulation.py your_race_course_data.csv --runners 1500 --single_track_config single_track_definitions.json

# Output
A CSV file like congestion_sim_results_1500runners.csv will be generated.
```

### **Step 3: Analyze the Simulation Results**

Use the two analysis scripts to visualize the data generated in Step 2.

#### **Runner Distribution Snapshot Analysis**

This script shows where runners are distributed on the course at specific moments in time.

**Command**

```shell
python src/runner_distribution_analysis.py [simulation_results.csv] [course_data.csv] [options]
```

**Options**

* -t, --times: Specify snapshot times in hours, separated by spaces. (Default: 3 10)

**Example (Analyzing the distribution at 15 and 20 hours into the race)**

```shell
python src/runner_distribution_analysis.py congestion_sim_results_1500runners.csv your_race_course_data.csv --times 15 20

# Output  
An image file like runner_distribution_snapshot_1500runners_active.png will be created.
```

#### **Aid Station Congestion Analysis**

This script analyzes the peak congestion times at specific locations (checkpoints or aid stations).

**Command**

```shell
python src/aid_station_analysis.py [simulation_results.csv] [options]
```

**Options**

* -s, --stations: Specify checkpoint distances in km, separated by spaces. (Default: 25 50 75 95)  
* -o, --output: Specify the output filename. (Default: aid_station_congestion.png)

**Example (Analyzing congestion at the 30km, 60km, and 90km marks)**

```shell
python src/aid_station_analysis.py congestion_sim_results_1500runners.csv --stations 30 60 90

# Output  
A graph image like aid_station_congestion.png will be created.
```

#### **Dot Animation Map Generation**

This script generates a standalone HTML file that visualizes the race as an animation with runners represented as moving dots on a map.

**Command**

```shell
python src/create_dot_animation.py [simulation_results.csv] [course_data.csv] [options]
```

**Options**

*   `-o, --output`: Output HTML file name (Default: `dot_animation.html`).
*   `--time_step`: Time step in minutes for animation frames (Default: 10).
*   `--max_runners`: Maximum number of runners to display on the map to prevent browser lag (Default: 300).

**Example**

```shell
python src/create_dot_animation.py congestion_sim_results_1500runners.csv your_race_course_data.csv --time_step 5 --max_runners 500

# Output
A standalone HTML file named dot_animation.html (or as specified) will be created. You can open this file in a web browser to view the animation.
```

## **License**

This project is released under the [MIT License](https://www.google.com/search?q=LICENSE).
