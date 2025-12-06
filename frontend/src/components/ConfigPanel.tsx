import React from 'react';
import classNames from 'classnames';

export interface ConfigState {
  difficulty: string;
  cardType: string;
  totalCards: number;
}

interface ConfigPanelProps {
  config: ConfigState;
  onChange: (newConfig: ConfigState) => void;
  onReset: () => void;
}

const DIFFICULTIES = ['Beginner', 'Intermediate', 'Advanced', 'Mixed'];
const CARD_TYPES = ['Standard', 'Multiple Choice', 'True/False', 'Mixed'];

const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, onChange, onReset }) => {
  
  const handleDifficultyChange = (diff: string) => {
    onChange({ ...config, difficulty: diff });
  };

  const handleTypeChange = (type: string) => {
    onChange({ ...config, cardType: type });
  };

  const handleTotalChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value);
    if (!isNaN(val) && val >= 1 && val <= 100) {
      onChange({ ...config, totalCards: val });
    }
  };

  return (
    <div className="card config-panel">
      <div className="section-title">Configuration</div>
      
      <div className="config-grid">
        <div className="input-group">
          <label>Difficulty Level</label>
          <div className="btn-group" role="group" aria-label="Difficulty selection">
            {DIFFICULTIES.map((diff) => (
              <button
                key={diff}
                className={classNames('btn btn-outline', { active: config.difficulty === diff })}
                onClick={() => handleDifficultyChange(diff)}
              >
                {diff}
              </button>
            ))}
          </div>
        </div>

        <div className="input-group">
          <label>Card Type</label>
          <div className="btn-group" role="group" aria-label="Card type selection">
            {CARD_TYPES.map((type) => (
              <button
                key={type}
                className={classNames('btn btn-outline', { active: config.cardType === type })}
                onClick={() => handleTypeChange(type)}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        <div className="input-group">
          <label htmlFor="total-cards">Total Cards (1-100)</label>
          <input
            type="number"
            id="total-cards"
            className="form-control"
            min="1"
            max="100"
            value={config.totalCards}
            onChange={handleTotalChange}
            style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ced4da' }}
          />
        </div>
      </div>

      <div style={{ marginTop: '1rem', textAlign: 'right' }}>
        <button className="btn btn-secondary" onClick={onReset}>
          Reset Filters
        </button>
      </div>
    </div>
  );
};

export default ConfigPanel;
