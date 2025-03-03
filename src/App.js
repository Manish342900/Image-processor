import React, { useEffect, useState } from 'react';
import axios from 'axios';
import "./App.css";

function App() {
  const [files, setFile] = useState([]);
  const [data, setData] = useState([]);
  const [totalSales, setTotalSales] = useState(0);
  const [totalRej, setTotalRej] = useState(0);
  const [totalCounter, setTotalCounter] = useState(0);
  const [counter, setCounter] = useState(0);

  const handleFileChange = (event) => {
    setFile(Array.from(event.target.files));
  };

  // Function to handle total calculation
  const handleTotal = () => {
    let sales = 0;
    let rej = 0;
    let count = 0;
    let counterSum = 0;

    data.forEach((row) => {
      sales += row["Billing Amount"];
      rej += row["Rejection Amount"];
      count += row.Count;
      counterSum += row["Total Counter"];
    });

    setTotalSales(sales);
    setTotalRej(rej);
    setCounter(count);
    setTotalCounter(counterSum);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      alert("Please select at least one file.");
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      const response = await axios.post("http://127.0.0.1:5000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (Array.isArray(response.data)) {
        setData(response.data);
      } else {
        setData([]); // Prevent .map() error if response isn't an array
        alert("No valid data returned from server.");
      }
    } catch (error) {
      console.error("Error uploading files", error);
      alert("Error processing the images.");
    }
  };

  useEffect(() => {
    if (data.length > 0) {
      handleTotal();
    }
  }, [data]);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Store Data Extractor</h1>
      <input type="file" multiple onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>

      {Array.isArray(data) && data.length > 0 ? (
        <table border="1" style={{ marginTop: "20px", width: "50%" }}>
          <thead>
            <tr>
              <th>Store</th>
              <th>Sales</th>
              <th>Rej %</th>
              <th>Counter</th>
              <th>Total Counter</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={index}
                style={
                  row.Store === "Total" ? { fontWeight: "bold", background: "#f0f0f0" } : {}
                }
              >
                <td>{row.Store}</td>
                <td>{row["Billing Amount"]}</td>
                <td>{row["Rejection Percentage"]}</td>
                <td>{row.Count}</td>
                <td>{row["Total Counter"]}</td>
              </tr>
            ))}
            <tr>
              <td className='grayy'>Total</td>
              <td className='grayy'>{totalSales}</td> {/* Rounds to two decimal places */}
              <td className='grayy'>{(totalRej / totalSales * 100).toFixed(2)}</td> {/* Rejection Percentage */}
              <td className='grayy'>{counter}</td>
              <td className='grayy'>{totalCounter}</td>
            </tr>
          </tbody>
        </table>
      ) : (
        <p>No data available. Upload an image to see results.</p>
      )}
    </div>
  );
}

export default App;
