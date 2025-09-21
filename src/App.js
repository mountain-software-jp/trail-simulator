import React, { useState } from 'react';
import './App.css';
import SetupTab from './components/SetupTab';
import SimulationTab from './components/SimulationTab';
import ResultsTab from './components/ResultsTab';
import { useParams } from './hooks/useParams';

function App() {
  const [activeTab, setActiveTab] = useState('setup');
  const [isAnalysisRunning, setIsAnalysisRunning] = useState(false);
  const [analysisProgressText, setAnalysisProgressText] = useState('Preparing...');
  const {
    courseCsvPath,
    setCourseCsvPath,
    simulationCsvPath,
    setSimulationCsvPath,
    paramsJson,
    setParamsJson,
    cutoffs,
    singleTracks,
    snapshotTimes,
    formData,
    setFormData,
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
  } = useParams();

  const showTab = (tabName) => {
    setActiveTab(tabName);
  };

  const selectGPXFile = async () => {
    const result = await window.electronAPI.selectFile({
      filters: [{ name: 'GPX Files', extensions: ['gpx'] }]
    });
    if (!result.canceled) {
      document.getElementById('gpxFile').value = result.filePaths[0];
      await parseGPX();
    }
  };

  const parseGPX = async () => {
    const gpxPath = document.getElementById('gpxFile').value;
    if (!gpxPath) {
      alert('Please select a GPX file.');
      return;
    }

    try {
      const output = await window.electronAPI.runPythonScript('gpx_parser.py', [gpxPath]);
      setCourseCsvPath(gpxPath.replace('.gpx', '_course_data.csv'));
      document.getElementById('parseOutput').textContent = output;
      alert('Course data created successfully.');
    } catch (error) {
      document.getElementById('parseOutput').textContent = 'Error: ' + error.message;
    }
  };

  const runSimulation = async () => {
    if (!courseCsvPath) {
      alert('Please create course data first.');
      return;
    }

    generateJsonFromForm();
    const params = paramsJson;
    try {
      await window.electronAPI.writeFile('project_params.json', params);
    } catch (error) {
      alert('Failed to save parameters: ' + error.message);
      return;
    }

    const btn = document.getElementById('runSimBtn');
    const progress = document.getElementById('simProgress');
    const progressText = document.getElementById('progressText');

    btn.disabled = true;
    progress.style.display = 'block';
    progressText.textContent = 'Running simulation...';

    try {
      const output = await window.electronAPI.runPythonScript('single_track_simulation.py', [courseCsvPath, 'project_params.json']);
      setSimulationCsvPath('congestion_sim_results_500runners.csv');
      document.getElementById('simOutput').textContent = output;
      progressText.textContent = 'Completed';
    } catch (error) {
      document.getElementById('simOutput').textContent = 'Error: ' + error.message;
      progressText.textContent = 'Error';
    } finally {
      btn.disabled = false;
    }
  };

  const runAnalysis = async () => {
    if (!simulationCsvPath) {
      alert('Please run simulation first.');
      return;
    }

    setIsAnalysisRunning(true);
    setAnalysisProgressText('Running runner distribution analysis...');

    try {
      const distOutput = await window.electronAPI.runPythonScript('runner_distribution_analysis.py', [simulationCsvPath, courseCsvPath, 'project_params.json']);
      setAnalysisProgressText('Running aid station analysis...');
      const aidOutput = await window.electronAPI.runPythonScript('aid_station_analysis.py', [simulationCsvPath, 'project_params.json']);
      setAnalysisProgressText('Creating dot animation...');
      const animOutput = await window.electronAPI.runPythonScript('create_dot_animation.py', [simulationCsvPath, courseCsvPath, 'project_params.json']);

      document.getElementById('analysisOutput').textContent = distOutput + '\n' + aidOutput + '\n' + animOutput;
      setAnalysisProgressText('Displaying results...');

      await displayResults();
      setAnalysisProgressText('Completed');
    } catch (error) {
      document.getElementById('analysisOutput').textContent = 'Error: ' + error.message;
      setAnalysisProgressText('Error');
    } finally {
      setIsAnalysisRunning(false);
    }
  };

  const displayResults = async () => {
    const imageContainer = document.getElementById('imageContainer');
    const animationContainer = document.getElementById('animationContainer');

    imageContainer.innerHTML = '';
    animationContainer.innerHTML = '';

    // アプリケーションパスを取得
    const appPath = await window.electronAPI.getAppPath();

    // 動的にファイル名を決定
    const imageFiles = [
      `runner_distribution_snapshot_${formData.runners}.png`,
      'aid_station_congestion.png'
    ];

    for (const file of imageFiles) {
      const exists = await window.electronAPI.fileExists(file);
      if (exists) {
        const displayName = file.replace(/_/g, ' ').replace('.png', '').replace(/\b\w/g, l => l.toUpperCase());
        // Electron でローカルファイルを表示するために file:// プロトコルを使用
        const fileUrl = `file://${appPath}/${file}`;
        imageContainer.innerHTML += `<div class="result-item"><h4>${displayName}</h4><img src="${fileUrl}" alt="${file}" style="max-width: 100%; height: auto;"></div>`;
      }
    }

    const animationFile = 'dot_animation.html';
    const animExists = await window.electronAPI.fileExists(animationFile);
    if (animExists) {
      // アニメーションファイルも file:// プロトコルを使用
      const animUrl = `file://${appPath}/${animationFile}`;
      animationContainer.innerHTML = `<div class="result-item"><h4>Dot Animation</h4><iframe src="${animUrl}" style="width: 100%; height: 600px; border: none;"></iframe></div>`;
    }
  };

  return (
    <div className="container">
      <h1>Trail Running Race Congestion Simulator</h1>

      <div className="tabs">
        <button className={`tab-button ${activeTab === 'setup' ? 'active' : ''}`} onClick={() => showTab('setup')}>Setup</button>
        <button className={`tab-button ${activeTab === 'simulation' ? 'active' : ''}`} onClick={() => showTab('simulation')}>Simulation</button>
        <button className={`tab-button ${activeTab === 'results' ? 'active' : ''}`} onClick={() => showTab('results')}>Results</button>
      </div>

      {activeTab === 'setup' && (
        <SetupTab
          selectGPXFile={selectGPXFile}
          courseCsvPath={courseCsvPath}
          simulationCsvPath={simulationCsvPath}
          paramsJson={paramsJson}
          cutoffs={cutoffs}
          singleTracks={singleTracks}
          snapshotTimes={snapshotTimes}
          formData={formData}
          setFormData={setFormData}
          importParams={importParams}
          exportParams={exportParams}
          saveParams={saveParams}
          addCutoff={addCutoff}
          removeCutoff={removeCutoff}
          updateCutoff={updateCutoff}
          addTrack={addTrack}
          removeTrack={removeTrack}
          updateTrack={updateTrack}
          addSnapshotTime={addSnapshotTime}
          removeSnapshotTime={removeSnapshotTime}
          updateSnapshotTime={updateSnapshotTime}
        />
      )}

      {activeTab === 'simulation' && (
        <SimulationTab runSimulation={runSimulation} />
      )}

      {activeTab === 'results' && (
        <ResultsTab
          runAnalysis={runAnalysis}
          isRunning={isAnalysisRunning}
          progressText={analysisProgressText}
        />
      )}
    </div>
  );
}

export default App;
