import React from 'react';

function ChatMessage({ message }) {
  const { role, content } = message;

  if (role === 'user') {
    return (
      <div className="message user">
        <div className="message-content">
          {content}
        </div>
      </div>
    );
  }

  if (role === 'assistant') {
    const { sql_query, data, columns, rows } = content;

    return (
      <div className="message assistant">
        <div className="message-content">
          <div className="query-content">
            <div className="query-label">SQL Query:</div>
            <div className="query-display">{sql_query}</div>
          </div>

          {rows > 0 && (
            <div className="results-section">
              <div className="query-label" style={{ marginTop: '12px' }}>
                Results ({rows} rows):
              </div>
              <table className="results-table">
                <thead>
                  <tr>
                    {columns.map(col => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.slice(0, 10).map((row, idx) => (
                    <tr key={idx}>
                      {columns.map(col => (
                        <td key={col}>
                          {row[col] !== null && row[col] !== undefined
                            ? String(row[col])
                            : 'NULL'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {rows > 10 && (
                <div className="query-label" style={{ marginTop: '8px', color: '#999' }}>
                  Showing 10 of {rows} rows
                </div>
              )}
            </div>
          )}

          {rows === 0 && (
            <div className="query-label" style={{ marginTop: '12px', color: '#999' }}>
              No results found
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
}

export default ChatMessage;
