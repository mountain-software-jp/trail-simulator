import React from 'react';

function ResultsTab({ runAnalysis }) {
  return (
    <div id="results" className="tab-content active">
      <div className="section">
        <h2>Step 4: Analysis Results</h2>
        <button onClick={runAnalysis}>Run Analysis</button>
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
