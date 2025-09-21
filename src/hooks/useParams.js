import { useState, useEffect } from 'react';

export function useParams() {
  const [courseCsvPath, setCourseCsvPath] = useState('');
  const [simulationCsvPath, setSimulationCsvPath] = useState('');
  const [paramsJson, setParamsJson] = useState('');
  const [cutoffs, setCutoffs] = useState([
    { distance: 39, time: 10 },
    { distance: 66, time: 15 },
    { distance: 87, time: 23.5 }
  ]);
  const [singleTracks, setSingleTracks] = useState([
    { start: 5, end: 8, capacity: 2 },
    { start: 20, end: 22.5, capacity: 1 },
    { start: 35.5, end: 38, capacity: 1 }
  ]);
  const [snapshotTimes, setSnapshotTimes] = useState([]);

  useEffect(() => {
    loadParams();
  }, []);

  const loadParams = async () => {
    try {
      const result = await window.electronAPI.readFile('project_params.json');
      if (result.success) {
        setParamsJson(result.content);
        loadFormFromJson(result.content);
      } else {
        loadDefaultParams();
      }
    } catch (error) {
      loadDefaultParams();
    }
  };

  const loadDefaultParams = () => {
    const defaultParams = {
      "simulation": {
        "settings": {
          "runners": 500,
          "avg_pace_min_per_km": 12,
          "std_dev_pace": 1.5,
          "time_limit_hours": 24
        },
        "wave_start": {
          "groups": 0,
          "interval_minutes": 0
        },
        "cutoffs": [],
        "single_track_sections": []
      },
      "analysis": {
        "runner_distribution": {
          "snapshot_times_hours": [],
          "output_filename": "runner_distribution_snapshot.png"
        },
        "aid_station": {
          "stations_km": [],
          "output_filename": "aid_station_congestion.png"
        },
        "dot_animation": {
          "output_filename": "dot_animation.html",
          "time_step_minutes": 15,
          "max_runners_to_display": 500
        }
      }
    };
    setParamsJson(JSON.stringify(defaultParams, null, 2));
  };

  const importParams = async () => {
    const result = await window.electronAPI.selectFile({
      filters: [{ name: 'JSON Files', extensions: ['json'] }]
    });
    if (!result.canceled) {
      try {
        const fileResult = await window.electronAPI.readFile(result.filePaths[0]);
        if (fileResult.success) {
          setParamsJson(fileResult.content);
          loadFormFromJson(fileResult.content);
          alert('Parameters imported successfully.');
        } else {
          alert('Failed to read file: ' + fileResult.error);
        }
      } catch (error) {
        alert('Error importing parameters: ' + error.message);
      }
    }
  };

  const exportParams = () => {
    generateJsonFromForm();
    const params = paramsJson;
    try {
      JSON.parse(params);
      window.electronAPI.saveFile({
        filters: [{ name: 'JSON Files', extensions: ['json'] }],
        defaultPath: 'project_params.json'
      }).then(result => {
        if (!result.canceled) {
          window.electronAPI.writeFile(result.filePath, params).then(writeResult => {
            if (writeResult.success) {
              alert('Parameters exported successfully.');
            } else {
              alert('Failed to export: ' + writeResult.error);
            }
          }).catch(error => {
            alert('Error writing file: ' + error.message);
          });
        }
      }).catch(error => {
        alert('Error saving file: ' + error.message);
      });
    } catch (error) {
      alert('Invalid JSON format: ' + error.message);
    }
  };

  const saveParams = () => {
    generateJsonFromForm();
    const params = paramsJson;
    try {
      JSON.parse(params);
      window.electronAPI.writeFile('project_params.json', params).then(result => {
        if (result.success) {
          alert('Parameters saved successfully.');
        } else {
          alert('Failed to save: ' + result.error);
        }
      }).catch(error => {
        alert('Error saving: ' + error.message);
      });
    } catch (error) {
      alert('Invalid JSON format.');
    }
  };

  const addCutoff = () => {
    setCutoffs([...cutoffs, { distance: '', time: '' }]);
  };

  const removeCutoff = (index) => {
    setCutoffs(cutoffs.filter((_, i) => i !== index));
  };

  const updateCutoff = (index, field, value) => {
    const newCutoffs = [...cutoffs];
    newCutoffs[index][field] = value;
    setCutoffs(newCutoffs);
  };

  const addTrack = () => {
    setSingleTracks([...singleTracks, { start: '', end: '', capacity: 2 }]);
  };

  const removeTrack = (index) => {
    setSingleTracks(singleTracks.filter((_, i) => i !== index));
  };

  const updateTrack = (index, field, value) => {
    const newTracks = [...singleTracks];
    newTracks[index][field] = value;
    setSingleTracks(newTracks);
  };

  const addSnapshotTime = () => {
    setSnapshotTimes([...snapshotTimes, '']);
  };

  const removeSnapshotTime = (index) => {
    setSnapshotTimes(snapshotTimes.filter((_, i) => i !== index));
  };

  const updateSnapshotTime = (index, value) => {
    const newTimes = [...snapshotTimes];
    newTimes[index] = value;
    setSnapshotTimes(newTimes);
  };

  const generateJsonFromForm = () => {
    try {
      const runners = parseInt(document.getElementById('runners').value) || 500;
      const avgPace = parseFloat(document.getElementById('avgPace').value) || 11;
      const stdDev = parseFloat(document.getElementById('stdDev').value) || 1.5;
      const timeLimit = parseInt(document.getElementById('timeLimit').value) || 26;
      const waveGroups = parseInt(document.getElementById('waveGroups').value) || 3;
      const waveInterval = parseInt(document.getElementById('waveInterval').value) || 10;
      const timeStep = parseInt(document.getElementById('timeStep').value) || 15;
      const maxRunners = parseInt(document.getElementById('maxRunners').value) || 500;

      const params = {
        simulation: {
          settings: {
            runners: runners,
            avg_pace_min_per_km: avgPace,
            std_dev_pace: stdDev,
            time_limit_hours: timeLimit
          },
          wave_start: {
            groups: waveGroups,
            interval_minutes: waveInterval
          },
          cutoffs: cutoffs.filter(c => c.distance && c.time).map(c => ({
            distance_km: parseFloat(c.distance),
            time_hours: parseFloat(c.time)
          })),
          single_track_sections: singleTracks.filter(t => t.start && t.end).map(t => ({
            range_km: [parseFloat(t.start), parseFloat(t.end)],
            capacity: parseInt(t.capacity)
          }))
        },
        analysis: {
          runner_distribution: {
            snapshot_times_hours: snapshotTimes.filter(t => t).map(t => parseFloat(t)),
            output_filename: `runner_distribution_snapshot_${runners}.png`
          },
          aid_station: {
            stations_km: cutoffs.slice(0, 3).map(c => parseFloat(c.distance)),
            output_filename: "aid_station_congestion.png"
          },
          dot_animation: {
            output_filename: "dot_animation.html",
            time_step_minutes: timeStep,
            max_runners_to_display: maxRunners
          }
        }
      };

      setParamsJson(JSON.stringify(params, null, 2));
    } catch (error) {
      alert('Error in generateJsonFromForm: ' + error.message);
    }
  };

  const loadFormFromJson = (jsonText) => {
    try {
      const params = JSON.parse(jsonText);

      if (params.simulation?.settings) {
        document.getElementById('runners').value = params.simulation.settings.runners || 500;
        document.getElementById('avgPace').value = params.simulation.settings.avg_pace_min_per_km || 11;
        document.getElementById('stdDev').value = params.simulation.settings.std_dev_pace || 1.5;
        document.getElementById('timeLimit').value = params.simulation.settings.time_limit_hours || 26;
      }

      if (params.simulation?.wave_start) {
        document.getElementById('waveGroups').value = params.simulation.wave_start.groups ?? 0;
        document.getElementById('waveInterval').value = params.simulation.wave_start.interval_minutes ?? 0;
      }

      if (params.simulation?.cutoffs) {
        setCutoffs(params.simulation.cutoffs.map(c => ({ distance: c.distance_km, time: c.time_hours })));
      }

      if (params.simulation?.single_track_sections) {
        setSingleTracks(params.simulation.single_track_sections.map(t => ({
          start: t.range_km[0],
          end: t.range_km[1],
          capacity: t.capacity
        })));
      }

      if (params.analysis?.dot_animation) {
        document.getElementById('timeStep').value = params.analysis.dot_animation.time_step_minutes || 15;
        document.getElementById('maxRunners').value = params.analysis.dot_animation.max_runners_to_display || 500;
      }

      if (params.analysis?.runner_distribution?.snapshot_times_hours) {
        setSnapshotTimes(params.analysis.runner_distribution.snapshot_times_hours.map(t => t.toString()));
      }
    } catch (error) {
      // Silent error
    }
  };

  return {
    courseCsvPath,
    setCourseCsvPath,
    simulationCsvPath,
    setSimulationCsvPath,
    paramsJson,
    setParamsJson,
    cutoffs,
    singleTracks,
    snapshotTimes,
    importParams,
    exportParams,
    saveParams,
    addCutoff,
    removeCutoff,
    updateCutoff,
    addTrack,
    removeTrack,
    updateTrack,
    addSnapshotTime,
    removeSnapshotTime,
    updateSnapshotTime,
    generateJsonFromForm
  };
}
