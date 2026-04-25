import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import Sidebar from './components/Sidebar';

import './App.css';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Create new session on initial load
  useEffect(() => {
    createNewSession();
  }, []);

  const createNewSession = async () => {
    try {
      setError(null);
      const response = await axios.post(`${API_URL}/sessions`);
      if (response.data.success) {
        const sessionId = response.data.session_id;
        setSessions(prev => [...prev, sessionId]);
        setActiveSession(sessionId);
        setMessages([]);
        setTables([]);
        setSelectedTable(null);
      }
    } catch (err) {
      setError('Failed to create session. Make sure the backend is running on http://localhost:5000');
    }
  };

  const loadSession = async (sessionId) => {
    try {
      setError(null);
      const response = await axios.get(`${API_URL}/sessions/${sessionId}`);
      if (response.data.success) {
        setActiveSession(sessionId);
        setMessages(response.data.messages || []);
        setTables(response.data.tables || []);
        if (response.data.tables.length > 0) {
          setSelectedTable(response.data.tables[0]);
        }
      }
    } catch (err) {
      setError('Failed to load session');
    }
  };

  const handleFileUpload = async (file) => {
    if (!activeSession || !file) return;

    try {
      setError(null);
      setLoading(true);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', activeSession);

      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        const tableName = response.data.table_name;
        const summaryData = response.data.summary_data;
        
        setTables(prev => [...prev, tableName]);
        setSelectedTable(tableName);
        
        // Add summary to chat
        const summaryMessage = {
          role: 'assistant',
          content: summaryData,
          timestamp: new Date().toISOString(),
          type: 'summary'
        };
        setMessages(prev => [...prev, summaryMessage]);
        
        // Automatically read out the summary for accessibility
        if ('speechSynthesis' in window) {
          window.speechSynthesis.cancel(); // Stop any ongoing speech
          const cleanSummary = summaryData.summary.replace(/[#*`_]/g, ''); // Remove common markdown characters
          const utterance = new SpeechSynthesisUtterance(cleanSummary);
          window.speechSynthesis.speak(utterance);
        }
        
        setSuccess(`File uploaded successfully! Created table: ${tableName}`);
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload file');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (message) => {
    if (!activeSession || !selectedTable || !message.trim()) return;

    try {
      setError(null);
      setLoading(true);

      // Add user message to chat
      const userMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, userMessage]);

      // Send message to backend
      const response = await axios.post(`${API_URL}/chat`, {
        session_id: activeSession,
        message: message,
        table_name: selectedTable,
      });

      if (response.data.success) {
        const assistantMessage = {
          role: 'assistant',
          content: {
            sql_query: response.data.sql_query,
            data: response.data.data,
            columns: response.data.columns,
            rows: response.data.rows,
            explanation: response.data.explanation,
            visualization: response.data.visualization,
            image_url: response.data.image_url,
          },
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to process message');
      // Remove the user message if there was an error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (e) => {
    setSelectedTable(e.target.value);
  };

  return (
    <div className="app-container">

      <Sidebar
        sessions={sessions}
        activeSession={activeSession}
        onNewChat={createNewSession}
        onSelectSession={loadSession}
      />

      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <div className="chat-title">
            SQL Chatbot - Natural Language Database Interface
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="chat-content">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              {success}
            </div>
          )}

          {messages.length === 0 && !error ? (
            <div className="empty-state">
              <div className="empty-state-icon">💬</div>
              <div className="empty-state-text">Start a conversation</div>
              <div className="empty-state-subtext">
                Upload a CSV or Excel file and ask questions about your data
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} />
            ))
          )}

          {loading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="loading-spinner"></div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="chat-input-area">
          {tables.length > 0 && (
            <div className="table-selector">
              <select value={selectedTable || ''} onChange={handleTableChange}>
                <option value="">Select a table</option>
                {tables.map(table => (
                  <option key={table} value={table}>
                    {table}
                  </option>
                ))}
              </select>
            </div>
          )}

          <ChatInput
            onFileUpload={handleFileUpload}
            onSendMessage={handleSendMessage}
            canUpload={Boolean(activeSession) && !loading}
            canSend={Boolean(selectedTable) && !loading}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
