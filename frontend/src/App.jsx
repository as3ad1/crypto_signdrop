import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API = 'http://localhost:5000/api';

function App() {
  const [users, setUsers] = useState([]);
  const [currentUser, setCurrentUser] = useState('');
  const [newUserName, setNewUserName] = useState('');
  const [content, setContent] = useState('');
  const [receiver, setReceiver] = useState('');
  const [filename, setFilename] = useState('file.txt');
  const [fileId, setFileId] = useState('');
  const [sender, setSender] = useState('');
  const [result, setResult] = useState('');

  // Register User
  const registerUser = async () => {
    if (!newUserName) return alert('Enter name');
    try {
      await axios.post(`${API}/register`, { name: newUserName });
      setUsers([...users, newUserName]);
      setNewUserName('');
      setResult(`✅ ${newUserName} registered!`);
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  // Send File
  const sendFile = async () => {
    if (!currentUser || !receiver || !content) return alert('Fill all fields');
    try {
      const res = await axios.post(`${API}/send-file`, {
        sender: currentUser,
        receiver,
        content,
        filename
      });
      setResult(`✅ File sent! ID: ${res.data.file_id.substring(0, 12)}...`);
      setContent('');
    } catch (err) {
      setResult(`❌ Error: ${err.response?.data?.message || err.message}`);
    }
  };

  // Receive File
  const receiveFile = async () => {
    if (!currentUser || !fileId) return alert('Fill all fields');
    try {
      const res = await axios.post(`${API}/receive-file`, {
        receiver: currentUser,
        file_id: fileId
      });
      setResult(`✅ File received!\nContent: ${res.data.content}\nSignature Valid: ${res.data.signature_valid}`);
      setFileId('');
    } catch (err) {
      setResult(`❌ Error: ${err.response?.data?.message || err.message}`);
    }
  };

  // Revoke File
  const revokeFile = async () => {
    if (!fileId) return alert('Enter file ID');
    try {
      await axios.post(`${API}/revoke/${fileId}`);
      setResult('✅ File revoked!');
      setFileId('');
    } catch (err) {
      setResult(`❌ Error: ${err.response?.data?.message || err.message}`);
    }
  };

  return (
    <div className="app">
      <h1>🔐 Signdrop - Simple Secure File Sharing</h1>

      {/* User Management */}
      <div className="panel">
        <h2>👥 Users</h2>
        <div className="input-group">
          <input
            placeholder="Enter username"
            value={newUserName}
            onChange={(e) => setNewUserName(e.target.value)}
          />
          <button onClick={registerUser}>Register</button>
        </div>
        <div className="users">
          {users.map((u) => (
            <button
              key={u}
              className={u === currentUser ? 'user active' : 'user'}
              onClick={() => setCurrentUser(u)}
            >
              {u} {u === currentUser && '✓'}
            </button>
          ))}
        </div>
      </div>

      {currentUser && (
        <>
          {/* Send File */}
          <div className="panel">
            <h2>📤 Send File (as {currentUser})</h2>
            <select value={receiver} onChange={(e) => setReceiver(e.target.value)}>
              <option value="">Select recipient...</option>
              {users.filter((u) => u !== currentUser).map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
            <input
              placeholder="Filename"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
            />
            <textarea
              placeholder="File content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows="4"
            />
            <button onClick={sendFile}>Send Encrypted File</button>
          </div>

          {/* Receive File */}
          <div className="panel">
            <h2>📥 Receive File (as {currentUser})</h2>
            <input
              placeholder="Enter File ID"
              value={fileId}
              onChange={(e) => setFileId(e.target.value)}
            />
            <button onClick={receiveFile}>Receive & Verify</button>
            <button onClick={revokeFile} style={{ marginLeft: '10px', background: '#dc2626' }}>
              Revoke File
            </button>
          </div>
        </>
      )}

      {/* Results */}
      {result && (
        <div className="panel result">
          <pre>{result}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
