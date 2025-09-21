import React from 'react';

function SimulationTab({ runSimulation }) {
  return (
    <div id="simulation" className="tab-content active">
      <div className="section">
        <h2>Step 3: Run Simulation</h2>
        <button id="runSimBtn" onClick={runSimulation}>Run Simulation</button>
        <div className="progress" id="simProgress">
          <progress value="0" max="100"></progress>
          <span id="progressText">Preparing...</span>
        </div>
        <div id="simOutput" className="output"></div>
      </div>
    </div>
  );
}

export default SimulationTab;
