import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_URL = 'http://localhost:8000/query';
  const API_TOKEN = 'mysecrettoken123';

  const handleSubmit = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }
    setLoading(true);
    setError('');
    setResponse(null);

    try {
      const res = await axios.post(
        API_URL,
        { query: query },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_TOKEN}`,
          },
        }
      );
      setResponse(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div className="App">
      <div className="container">
        <h1>🤖 LLM Chatbot</h1>
        <p className="subtitle">Ask anything about customers in natural language</p>

        <div className="input-section">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="e.g., Show me all female customers from Mumbai"
            className="query-input"
          />
          <button onClick={handleSubmit} disabled={loading} className="submit-btn">
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </div>

        <div className="examples">
          <p><strong>Try:</strong></p>
          <ul>
            <li>Show me all female customers from Mumbai</li>
            <li>List all male customers</li>
            <li>How many customers are from Bangalore?</li>
            <li>Show all customers</li>
          </ul>
        </div>

        {error && <div className="error">❌ {error}</div>}

        {response && (
          <div className="results">
            <h2>Results</h2>
            <div className="sql-box">
              <strong>Generated SQL:</strong>
              <code>{response.generated_sql}</code>
            </div>
            <p><strong>Found {response.count} result(s)</strong></p>
            {response.results.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    {Object.keys(response.results[0]).map((key) => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {response.results.map((row, idx) => (
                    <tr key={idx}>
                      {Object.values(row).map((val, i) => (
                        <td key={i}>{String(val)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No results found.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
