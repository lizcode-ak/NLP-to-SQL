import ReactMarkdown from 'react-markdown';
import DataChart from './DataChart';

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
    // 1. Handle Simple string message (Legacy or fallback)
    if (typeof content === 'string') {
      const formattedContent = content.replace(
        />\s*\[!(NOTE|WARNING|IMPORTANT|CAUTION|TIP)\]/gi,
        (match, type) => {
          const title = type.charAt(0).toUpperCase() + type.slice(1).toLowerCase();
          return `> **${title}:**`;
        }
      );

      return (
        <div className="message assistant">
          <div style={{ color: "red", fontWeight: "bold" }}>
            TEST CHATMESSAGE LOADED
          </div>
          <div className="message-content">
            <ReactMarkdown>{formattedContent}</ReactMarkdown>
          </div>
        </div>
      );
    }

    // 2. Handle Summary object (New format: summary, visualization, data, columns)
    if (content.summary) {
      const { summary, visualization, data, columns } = content;
      return (
        <div className="message assistant">
          <div className="message-content">
            <div className="summary-display">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
            {content.image_url ? (
              <div style={{
                marginTop: "16px",
                padding: "12px",
                borderRadius: "12px",
                background: "#111827"
              }}>
                <div style={{
                  fontSize: "12px",
                  opacity: 0.7,
                  marginBottom: "8px"
                }}>
                  Generated Visualization
                </div>

                <img
                  src={`http://127.0.0.1:5000${content.image_url}`}
                  alt="Chart"
                  onLoad={() => console.log("Chart loaded")}
                  onError={(e) => console.log("Chart failed", e)}
                  style={{
                    width: "100%",
                    maxWidth: "720px",
                    display: "block",
                    borderRadius: "12px"
                  }}
                />
              </div>
            ) : (
              <div style={{ marginTop: "12px", opacity: 0.6 }}>
                No visualization image_url received
              </div>
            )}
            <div className="query-label" style={{ marginTop: '14px', fontSize: '11px', opacity: 0.6 }}>
              Initial Dataset Insight
            </div>
          </div>
        </div>
      );
    }

    // 3. Handle SQL Result object
    const { sql_query, data, columns, rows, explanation, visualization } = content;

    return (
      <div className="message assistant">
        <div className="message-content">
          <div className="query-content">
            <div className="query-label">SQL Query:</div>
            <div className="query-display">{sql_query}</div>
          </div>

          {content.image_url && (
            <div className="inline-chart-block">
              <div style={{
                marginTop: "16px",
                padding: "12px",
                borderRadius: "14px",
                background: "#111827"
              }}>
                <div style={{
                  fontSize: "12px",
                  opacity: 0.7,
                  marginBottom: "8px"
                }}>
                  Generated Visualization
                </div>

                <img
                  src={`http://127.0.0.1:5000${content.image_url}`}
                  alt="Generated Chart"
                  style={{
                    width: "100%",
                    maxWidth: "720px",
                    borderRadius: "12px",
                    display: "block"
                  }}
                />
              </div>
            </div>
          )}
          {!content.image_url && visualization && visualization.type && visualization.type !== 'none' && (
            <div className="inline-chart-block">
              <DataChart data={data} config={visualization} />
            </div>
          )}
          {explanation && (
            <div className="explanation-content">
              <ReactMarkdown>{explanation}</ReactMarkdown>
            </div>
          )}

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
