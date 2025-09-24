import React, { useEffect } from 'react';

function ResultsTab({ runAnalysis, isRunning, progressText, displayResults, simulationCsvPath }) {
  useEffect(() => {
    if (simulationCsvPath) {
      displayResults();
    }
  }, [displayResults, simulationCsvPath]);

  return (
    <div id="results" className="tab-content active">
      <div className="section">
        <h2>Step 4: Analysis Results</h2>
        <button onClick={runAnalysis} disabled={isRunning}>Run Analysis</button>
        <div className="progress" id="analysisProgress" style={{ display: isRunning ? 'block' : 'none' }}>
          <progress value="0" max="100"></progress>
          <span id="analysisProgressText">{progressText}</span>
        </div>
        <div id="analysisOutput" className="output"></div>
        <div id="resultsContainer">
          <h3 style={{ color: '#2c3e50', marginBottom: '20px', fontSize: '1.3em' }}>Generated Files</h3>
          <div className="results-grid" id="imageContainer"></div>
          <div className="results-grid" id="animationContainer"></div>
        </div>
      </div>
    </div>
  );
}

export default ResultsTab;
