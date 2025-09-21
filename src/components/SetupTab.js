import React from 'react';

function SetupTab({ selectGPXFile, courseCsvPath, simulationCsvPath, paramsJson, cutoffs, singleTracks, snapshotTimes, importParams, exportParams, saveParams, addCutoff, removeCutoff, updateCutoff, addTrack, removeTrack, updateTrack, addSnapshotTime, removeSnapshotTime, updateSnapshotTime }) {
  return (
    <div id="setup" className="tab-content active">
      <div className="section">
        <h2>Step 1: Create Course Data from GPX File</h2>
        <div className="file-input">
          <label>Select GPX File:</label>
          <input type="text" id="gpxFile" readOnly />
          <button onClick={selectGPXFile}>Choose File</button>
        </div>
        <div id="parseOutput" className="output"></div>
      </div>

      <div className="section">
        <h2>Step 2: Project Parameters Configuration</h2>
        <button onClick={importParams}>Import Parameters</button>
        <button onClick={exportParams}>Export Parameters</button>

        <div id="formEditor">
          <div className="param-section">
            <h3>Basic Simulation Settings</h3>
            <div className="form-grid">
              <div className="form-group">
                <label>Number of Runners:</label>
                <input type="number" id="runners" min="1" max="5000" defaultValue="500" />
              </div>
              <div className="form-group">
                <label>Average Pace (min/km):</label>
                <input type="number" id="avgPace" min="5" max="20" step="0.1" defaultValue="11" />
              </div>
              <div className="form-group">
                <label>Pace Standard Deviation:</label>
                <input type="number" id="stdDev" min="0" max="5" step="0.1" defaultValue="1.5" />
              </div>
              <div className="form-group">
                <label>Time Limit (hours):</label>
                <input type="number" id="timeLimit" min="1" max="48" defaultValue="26" />
              </div>
            </div>
          </div>

          <div className="param-section">
            <h3>Wave Start Settings</h3>
            <div className="form-grid">
              <div className="form-group">
                <label>Number of Wave Groups:</label>
                <input type="number" id="waveGroups" min="0" max="20" defaultValue="0" />
              </div>
              <div className="form-group">
                <label>Interval Between Waves (minutes):</label>
                <input type="number" id="waveInterval" min="0" max="60" defaultValue="0" />
              </div>
            </div>
          </div>

          <div className="param-section">
            <h3>Cutoff Points</h3>
            <p className="param-description">Set mandatory checkpoints where runners must pass by specific times. Runners who miss cutoffs are disqualified.</p>
            <div className="table-header">
              <span>Distance (km)</span>
              <span>Time Limit (hours)</span>
              <span>Action</span>
            </div>
            <div id="cutoffsContainer">
              {cutoffs.map((cutoff, index) => (
                <div key={index} className="cutoff-item">
                  <input
                    type="number"
                    placeholder="Distance (km)"
                    value={cutoff.distance}
                    onChange={(e) => updateCutoff(index, 'distance', e.target.value)}
                    min="0"
                    step="0.1"
                  />
                  <input
                    type="number"
                    placeholder="Time (hours)"
                    value={cutoff.time}
                    onChange={(e) => updateCutoff(index, 'time', e.target.value)}
                    min="0"
                    step="0.1"
                  />
                  <button onClick={() => removeCutoff(index)}>Remove</button>
                </div>
              ))}
            </div>
            <button onClick={addCutoff}>Add Cutoff Point</button>
          </div>

          <div className="param-section">
            <h3>Single Track Sections</h3>
            <p className="param-description">Define narrow trail sections where passing is difficult. Capacity determines how many runners can pass simultaneously.</p>
            <div className="table-header track-header">
              <span>Start (km)</span>
              <span>End (km)</span>
              <span>Capacity (1-2 runners)</span>
              <span>Action</span>
            </div>
            <div id="singleTracksContainer">
              {singleTracks.map((track, index) => (
                <div key={index} className="track-item">
                  <input
                    type="number"
                    placeholder="Start (km)"
                    value={track.start}
                    onChange={(e) => updateTrack(index, 'start', e.target.value)}
                    min="0"
                    step="0.1"
                  />
                  <input
                    type="number"
                    placeholder="End (km)"
                    value={track.end}
                    onChange={(e) => updateTrack(index, 'end', e.target.value)}
                    min="0"
                    step="0.1"
                  />
                  <select
                    value={track.capacity}
                    onChange={(e) => updateTrack(index, 'capacity', e.target.value)}
                  >
                    <option value="1">1 runner</option>
                    <option value="2">2 runners</option>
                  </select>
                  <button onClick={() => removeTrack(index)}>Remove</button>
                </div>
              ))}
            </div>
            <button onClick={addTrack}>Add Single Track Section</button>
          </div>

          <div className="param-section">
            <h3>Analysis Settings</h3>
            <div className="form-grid">
              <div className="form-group">
                <label>Animation Time Step (minutes):</label>
                <input type="number" id="timeStep" min="1" max="60" defaultValue="15" />
              </div>
              <div className="form-group">
                <label>Max Runners to Display:</label>
                <input type="number" id="maxRunners" min="10" max="2000" defaultValue="500" />
              </div>
            </div>
            <div className="form-group">
              <label>Snapshot Times (hours):</label>
              <p className="param-description">Times at which to take snapshots of runner distribution.</p>
              <div id="snapshotTimesContainer">
                {snapshotTimes.map((time, index) => (
                  <div key={index} className="cutoff-item">
                    <input
                      type="number"
                      placeholder="Time (hours)"
                      value={time}
                      onChange={(e) => updateSnapshotTime(index, e.target.value)}
                      min="0"
                      step="0.1"
                    />
                    <button onClick={() => removeSnapshotTime(index)}>Remove</button>
                  </div>
                ))}
              </div>
              <button onClick={addSnapshotTime}>Add Snapshot Time</button>
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <button onClick={saveParams}>Save Parameters</button>
          </div>
        </div>

        <textarea id="paramsJson" value={paramsJson} onChange={(e) => setParamsJson(e.target.value)} style={{ display: 'none' }} />
      </div>
    </div>
  );
}

export default SetupTab;
