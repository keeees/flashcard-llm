import React, { useState, useEffect } from 'react';

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
      <label htmlFor="source-text">源内容</label>
      <textarea
        id="source-text"
        value={value}
        onChange={handleChange}
        placeholder="在此输入或粘贴文本... (支持段落和列表)"
        aria-label="源内容输入"
      />
      <div className="char-count">
        {charCount} / {maxLength} 字符
      </div>
    </div>
  );
};

export default TextInput;
