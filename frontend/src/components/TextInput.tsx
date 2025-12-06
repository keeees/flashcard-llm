import React, { useState, useEffect, useCallback } from 'react';
import classNames from 'classnames';

interface TextInputProps {
  value: string;
  onChange: (value: string) => void;
  maxLength?: number;
}

const TextInput: React.FC<TextInputProps> = ({ value, onChange, maxLength = 50000 }) => {
  const [charCount, setCharCount] = useState(0);

  useEffect(() => {
    setCharCount(value.length);
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    if (newValue.length <= maxLength) {
      onChange(newValue);
    }
  };

  return (
    <div className="input-group">
      <label htmlFor="source-text">Source Content</label>
      <textarea
        id="source-text"
        value={value}
        onChange={handleChange}
        placeholder="Enter or paste your text data here... (Support for paragraphs and lists)"
        aria-label="Source text input"
      />
      <div className="char-count">
        {charCount} / {maxLength} characters
      </div>
    </div>
  );
};

export default TextInput;
