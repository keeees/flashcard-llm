import React, { useState } from 'react';
import TextInput from './TextInput';
import ConfigPanel, { ConfigState } from './ConfigPanel';
import { generateCards, Flashcard } from '../services/api';
import '../styles/main.scss';

const DEFAULT_CONFIG: ConfigState = {
  difficulty: 'Mixed',
  cardType: 'Standard',
  totalCards: 10,
};

const FlashcardGenerator: React.FC = () => {
  const [text, setText] = useState('');
  const [config, setConfig] = useState<ConfigState>(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(false);
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!text.trim()) {
      setError('请输入文本内容。');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const generatedCards = await generateCards({
        text,
        difficulty: config.difficulty,
        card_type: config.cardType,
        total_cards: config.totalCards
      });
      setCards(generatedCards);
    } catch (err) {
      setError('生成卡片失败，请检查网络连接并重试。');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (cards.length === 0) return;

    // Generate CSV content
    const headers = ['问题', '答案', '标签', '类型'];
    const rows = cards.map(c => [
      `"${c.question.replace(/"/g, '""')}"`,
      `"${c.answer.replace(/"/g, '""')}"`,
      `"${c.tags.join(', ')}"`,
      `"${c.type}"`
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    const date = new Date();
    const timestamp = date.toISOString().slice(0, 10).replace(/-/g, '') + '_' + 
                      date.toTimeString().slice(0, 4).replace(/:/g, '');
    const filename = `cards_${config.cardType.toLowerCase()}_${timestamp}.csv`;
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="container">
      <h1 style={{ textAlign: 'center', marginBottom: '2rem', color: '#007bff' }}>AI 闪卡生成器</h1>
      
      <div className="card">
        <TextInput value={text} onChange={setText} />
      </div>

      <ConfigPanel 
        config={config} 
        onChange={setConfig} 
        onReset={() => setConfig(DEFAULT_CONFIG)} 
      />

      <div className="download-section">
        {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}
        
        <button 
          className="btn btn-primary" 
          onClick={handleGenerate} 
          disabled={loading || !text.trim()}
          style={{ fontSize: '1.2rem', padding: '0.75rem 2rem' }}
        >
          {loading && <span className="loading-spinner"></span>}
          {loading ? '生成中...' : '生成闪卡'}
        </button>
      </div>

      {cards.length > 0 && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <div className="section-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>预览 ({cards.length})</span>
            <button className="btn btn-primary" onClick={handleDownload}>
              下载 CSV
            </button>
          </div>
          
          <div style={{ overflowX: 'auto' }}>
            <table className="preview-table">
              <thead>
                <tr>
                  <th>问题</th>
                  <th>答案</th>
                  <th>类型</th>
                  <th>标签</th>
                </tr>
              </thead>
              <tbody>
                {cards.map((card, idx) => (
                  <tr key={idx}>
                    <td>{card.question}</td>
                    <td>{card.answer}</td>
                    <td>{card.type}</td>
                    <td>{card.tags.join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default FlashcardGenerator;
