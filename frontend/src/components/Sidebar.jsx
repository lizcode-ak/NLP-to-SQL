import React from 'react';

function Sidebar({ sessions, activeSession, onNewChat, onSelectSession }) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          + New Chat
        </button>
      </div>

      <div className="sidebar-content">
        {sessions.map(sessionId => (
          <div
            key={sessionId}
            className={`chat-item ${activeSession === sessionId ? 'active' : ''}`}
            onClick={() => onSelectSession(sessionId)}
          >
            <span title={sessionId}>
              💬 {sessionId.slice(-8)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Sidebar;
