# **Trail Running Race Congestion Simulator**

This project is a suite of tools for simulating and analyzing runner traffic and congestion in trail running races using GPX course data and Monte Carlo methods.

It particularly aims for more realistic congestion prediction by modeling the traffic jams that occur on narrow single-track sections where overtaking is difficult. This helps race directors and organizers to evaluate the impact of participant numbers and start systems on the race dynamics, aiding in decision-making for the proper allocation of resources at aid stations.

*Runner distribution for a 1500-participant race at 15 and 20 hours (active runners only).*

## **Workflow**

The toolset consists of the following four steps (scripts):

[GPX File] -> (1. gpx_parser.py) -> [Course CSV] -> (2. single_track_simulation.py) -> [Simulation Result CSV] -> (3. & 4. Analysis Scripts) -> [Analysis Graphs]

1. **Convert GPX to CSV**: gpx_parser.py  
   * Reads a race's GPX file and generates course data in a CSV format suitable for analysis (including distance, elevation, gradient, etc.).  
2. **Simulation with Congestion Model**: single_track_simulation.py  
   * Simulates runner movements based on the course data and parameters (number of participants, average pace, etc.). It reproduces traffic jams by considering the capacity of single-track sections.  
3. **Runner Distribution Snapshot Analysis**: runner_distribution_analysis.py  
   * Visualizes the runner distribution at specified times as a histogram based on the simulation results. It helps to understand "where the main pack of runners is at what time."  
4. **Aid Station Congestion Analysis**: aid_station_analysis.py  
   * Analyzes the passage times of runners at specified points (e.g., aid stations) and visualizes the congestion level over time. It helps predict "which aid station will be most crowded and at what time."

## **Required Libraries**

To run these tools, you need the following Python libraries:

* gpxpy  
* pandas  
* numpy  
* matplotlib

You can install them all with the following command:

pip install gpxpy pandas numpy matplotlib

## **Usage**

### **Step 1: Convert GPX to Course Data CSV (gpx_parser.py)**

First, convert the race GPX file into CSV format.

**Command**

python gpx_parser.py [path/to/your/gpx_file.gpx]

**Example**

python gpx_parser.py kagaspa100.gpx

Output  
A file named something like kagaspa100_course_data.csv will be generated. This file is the foundation for the subsequent simulation and analysis.

### **Step 2: Run Simulation with Congestion Model (single_track_simulation.py)**

Next, run the congestion simulation using the generated course data.

Preparation  
Open single_track_simulation.py and edit the single_track_definitions list to match your race course.  

```shell
# Define the single-track sections according to your race course  
single_track_definitions = [  
    {'range_km': (5, 8), 'capacity': 2},    # From 5km to 8km, capacity is 2 people at a time  
    {'range_km': (20, 22.5), 'capacity': 1}, # From 20km to 22.5km, capacity is 1 person  
]
```

**Command**

```shell
python single_track_simulation.py [course_data.csv] [options]
```

**Options**

* -n, --runners: Number of runners (Default: 500)  
* -p, --avg_pace: Overall average pace in minutes/km (Default: 10.0)  
* -s, --std_dev: Standard deviation of pace (Default: 1.5)  
* -t, --time_limit: Time limit in hours (Default: 24)

**Example (1500 runners, 12 min/km avg pace, 30h time limit)**

```shell
python single_track_simulation.py kagaspa100_course_data.csv -n 1500 -p 12.0 -s 2.0 -t 30
``` 

Output:
```shell  
A CSV file like congestion_sim_results_1500runners.csv will be generated, containing time-series position data for all runners.
```

### **Step 3: Runner Distribution Snapshot Analysis (runner_distribution_analysis.py)**

Visualize the runner distribution at any given time using the simulation results.

**Command**

```shell
python runner_distribution_analysis.py [simulation_results.csv] [course_data.csv] [options]
```

**Options**

* -t, --times: Specify the hours to analyze, separated by spaces. (Default: 3 10)

**Example (Analyze distribution at 15 and 20 hours)**

```shell
python runner_distribution_analysis.py congestion_sim_results_1500runners.csv kagaspa100_course_data.csv -t 15 20
```

Output:  
```shell
A graph image like runner_distribution_snapshot_1500runners_active.png will be created.
```

### **Step 4: Aid Station Congestion Analysis (aid_station_analysis.py)**

Analyze the congestion peaks at aid stations using the simulation results.

Preparation  
Open aid_station_analysis.py and edit the aid_stations_km list to specify the locations (in km) you want to analyze.  
# Specify the aid station locations (km) to be analyzed  
aid_stations_km = [25.5, 51.3, 75.8]

**Command**

```shell
python aid_station_analysis.py [simulation_results.csv]
```

**Example**

```shell
python aid_station_analysis.py congestion_sim_results_1500runners.csv
``` 

Output  
```shell
A graph image like aid_station_congestion.png will be created, allowing you to check the peak congestion times for each aid station.
```

## **License**

This project is released under the [MIT License](https://www.google.com/search?q=LICENSE).