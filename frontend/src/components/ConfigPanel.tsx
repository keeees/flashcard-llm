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

const DIFFICULTIES = [
  { value: 'Beginner', label: '初级' },
  { value: 'Intermediate', label: '中级' },
  { value: 'Advanced', label: '高级' },
  { value: 'Mixed', label: '混合' }
];

const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, onChange, onReset }) => {
  
  const handleDifficultyChange = (diff: string) => {
    onChange({ ...config, difficulty: diff });
  };

  const handleTotalChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value);
    if (!isNaN(val) && val >= 1 && val <= 100) {
      onChange({ ...config, totalCards: val });
    }
  };

  return (
    <div className="card config-panel">
      <div className="section-title">配置选项</div>
      
      <div className="config-grid">
        <div className="input-group">
          <label>难度等级</label>
          <div className="btn-group" role="group" aria-label="难度选择">
            {DIFFICULTIES.map((diff) => (
              <button
                key={diff.value}
                className={classNames('btn btn-outline', { active: config.difficulty === diff.value })}
                onClick={() => handleDifficultyChange(diff.value)}
              >
                {diff.label}
              </button>
            ))}
          </div>
        </div>

        <div className="input-group">
          <label htmlFor="total-cards">生成数量 (1-100)</label>
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
          重置配置
        </button>
      </div>
    </div>
  );
};

export default ConfigPanel;
