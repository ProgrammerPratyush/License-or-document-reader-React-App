import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // Import the CSS file

function App() {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (file) {
      const formData = new FormData();
      formData.append("document", file);

      try {
        // const res = await axios.post("http://localhost:5000/upload", formData);
        const res = await axios.post("https://license-or-document-reader-react-app.onrender.com/upload", formData);
        setResponse(JSON.stringify(res.data, null, 2));
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <div className="container">
      <h1>Document Capture</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      <pre>{response}</pre>
    </div>
  );
}

export default App;
