import React, { useState, useRef } from 'react';

function ChatInput({ onFileUpload, onSendMessage, canUpload, canSend, loading }) {
  const [message, setMessage] = useState('');
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);

  // Initialize Speech Recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = SpeechRecognition ? new SpeechRecognition() : null;

  if (recognition) {
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      
      const newText = finalTranscript || interimTranscript;
      if (newText) {
        setMessage(prev => (prev.endsWith(' ') || !prev ? prev + newText : prev + ' ' + newText));
      }
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      setIsRecording(false);
    };
  }

  const toggleRecording = () => {
    if (!recognition) {
      alert('Speech recognition is not supported in this browser.');
      return;
    }

    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
      setIsRecording(true);
    }
  };


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
          title="Upload Data, Text, or Audio file"
        >
          +
        </button>
        <input
          ref={fileInputRef}
          id="file-input"
          type="file"
          onChange={handleFileChange}
          accept=".csv,.xlsx,.xls,.txt,.mp3,.wav,.png,.jpg,.jpeg,.webp"
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
        className={`mic-btn ${isRecording ? 'recording' : ''}`}
        onClick={toggleRecording}
        disabled={!canSend || loading}
        title={isRecording ? 'Stop Recording' : 'Voice Input'}
      >
        {isRecording ? '⏹' : '🎤'}
      </button>

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
