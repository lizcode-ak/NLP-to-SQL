import React, { useState, useRef } from 'react';

function ChatInput({ onFileUpload, onSendMessage, canUpload, canSend, loading }) {
  const [message, setMessage] = useState('');
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  const handleSend = () => {
    if (message.trim() && canSend && !loading) {
      onSendMessage(message);
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleTextareaChange = (e) => {
    setMessage(e.target.value);
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  };

  return (
    <div className="input-container">
      <div className="file-upload">
        <button
          className="upload-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={!canUpload}
          title="Upload CSV or Excel file"
        >
          +
        </button>
        <input
          ref={fileInputRef}
          id="file-input"
          type="file"
          onChange={handleFileChange}
          accept=".csv,.xlsx,.xls"
          disabled={!canUpload}
        />
      </div>

      <textarea
        ref={textareaRef}
        className="message-input"
        value={message}
        onChange={handleTextareaChange}
        onKeyDown={handleKeyDown}
        placeholder={canSend ? 'Ask a question about your data...' : 'Please upload a file first...'}
        disabled={!canSend}
        rows={1}
      />

      <button
        className="send-btn"
        onClick={handleSend}
        disabled={!canSend || !message.trim() || loading}
        title="Send message"
      >
        {loading ? '↻' : '→'}
      </button>
    </div>
  );
}

export default ChatInput;
