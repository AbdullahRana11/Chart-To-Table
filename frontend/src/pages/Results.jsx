import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Download, RefreshCw, CheckCircle, AlertTriangle, ArrowLeft, Edit2, Save } from 'lucide-react';
import { saveExtraction, updateExtraction } from '../utils/storage';
import styles from './Results.module.css';

const Results = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [extractionId, setExtractionId] = useState(null);

  useEffect(() => {
    // Check if coming from history with saved data
    if (location.state?.savedData) {
      setData(location.state.savedData);
      setExtractionId(location.state.savedData.id);
      setLoading(false);
      return;
    }

    if (!location.state?.file) {
      navigate('/upload');
      return;
    }

    // Create FormData
    const formData = new FormData();
    formData.append('file', location.state.file);

    fetch('http://localhost:5000/api/convert', {
      method: 'POST',
      body: formData,
    })
      .then(res => {
        if (!res.ok) throw new Error('Extraction failed');
        return res.json();
      })
      .then(apiData => {
        // Map backend response to frontend state
        // Backend returns: { success, data: [{}], columns: [], chart_type, accuracy: { score, ssim } }

        // Create rows from data array based on columns order
        const rows = apiData.data.map(row =>
          apiData.columns.map(col => row[col])
        );

        const extractionData = {
          confidence: apiData.accuracy?.score || 0,
          headers: apiData.columns || [],
          rows: rows,
          verificationImage: null, // Backend doesn't return this yet
          status: (apiData.accuracy?.score > 0.8) ? 'verified' : 'review needed',
          title: location.state.file.name || 'Extraction Results',
          filename: location.state.file.name,
          thumbnail: location.state.file.preview,
        };

        setData(extractionData);
        setLoading(false);

        // Save to history
        const saved = saveExtraction(extractionData);
        if (saved) {
          setExtractionId(saved.id);
        }
      })
      .catch(err => {
        console.error('API Error:', err);

        let errorMessage = 'Connection failed';
        if (err.name === 'AbortError') {
          errorMessage = 'Request timeout - Backend took too long to respond. Make sure the backend server is running.';
        } else if (err.message.includes('fetch')) {
          errorMessage = 'Cannot connect to backend. Please start the backend server: cd backend && python app.py';
        } else {
          errorMessage = err.message;
        }

        // Show error in table format
        setData({
          confidence: 0,
          headers: ['Error'],
          rows: [[errorMessage]],
          status: 'error',
          filename: location.state?.file?.name || 'Unknown',
          thumbnail: location.state?.file?.preview,
        });
        setLoading(false);
      });
  }, [location.state, navigate]);

  const handleCellEdit = (rowIndex, cellIndex, newValue) => {
    const updatedRows = [...data.rows];
    updatedRows[rowIndex][cellIndex] = newValue;
    setData({ ...data, rows: updatedRows });
  };

  const handleSave = () => {
    if (extractionId) {
      updateExtraction(extractionId, { rows: data.rows, headers: data.headers });
    }
    setIsEditing(false);
  };

  const handleDownloadJSON = () => {
    if (!data) return;
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = `extraction_${data.filename || "result"}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadCSV = () => {
    if (!data) return;
    const headers = data.headers.join(",");
    const rows = data.rows.map(row => row.join(",")).join("\n");
    const csvContent = headers + "\n" + rows;

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = `extraction_${data.filename || "result"}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const toggleEdit = () => {
    if (isEditing) {
      // Prompt to save changes
      if (window.confirm('Save changes before exiting edit mode?')) {
        handleSave();
      } else {
        setIsEditing(false);
      }
    } else {
      setIsEditing(true);
    }
  };

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <RefreshCw size={48} className={styles.spinner} />
        </motion.div>
        <p>Extracting data from chart...</p>
      </div>
    );
  }

  return (
    <div className="container">
      <motion.div
        className={styles.resultsWrapper}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className={styles.header}>
          <button onClick={() => navigate('/upload')} className={styles.backBtn}>
            <ArrowLeft size={20} /> Back
          </button>
          <h1>{data.title || 'Extraction Results'}</h1>
        </div>

        <div className={styles.grid}>
          <div className={`${styles.card} glass-panel`}>
            <div className={styles.cardHeader}>
              <h2>Extracted Data</h2>
              <div className={styles.actions}>
                <button
                  className={isEditing ? styles.saveBtn : styles.editBtn}
                  onClick={isEditing ? handleSave : toggleEdit}
                >
                  {isEditing ? (
                    <>
                      <Save size={16} />
                      Save
                    </>
                  ) : (
                    <>
                      <Edit2 size={16} />
                      Edit
                    </>
                  )}
                </button>
                <button className={styles.downloadBtn} onClick={handleDownloadCSV}>
                  <Download size={16} /> CSV
                </button>
                <button className={styles.downloadBtn} onClick={handleDownloadJSON}>
                  <Download size={16} /> JSON
                </button>
              </div>
            </div>
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    {data.headers.map((header, i) => (
                      <th key={i}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row, i) => (
                    <tr key={i}>
                      {row.map((cell, j) => (
                        <td
                          key={j}
                          className={isEditing ? styles.editable : ''}
                          contentEditable={isEditing}
                          suppressContentEditableWarning
                          onBlur={(e) => isEditing && handleCellEdit(i, j, e.target.textContent)}
                        >
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className={styles.sidebar}>
            <div className={`${styles.card} glass-panel`}>
              <h2>Confidence Score</h2>
              <div className={styles.scoreContainer}>
                <div className={styles.scoreCircle} style={{ '--score': data.confidence * 100 }}>
                  <svg viewBox="0 0 36 36" className={styles.circularChart}>
                    <path className={styles.circleBg} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    <path
                      className={styles.circle}
                      strokeDasharray={`${data.confidence * 100}, 100`}
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className={styles.scoreText}>
                    <span className={styles.scoreValue}>{Math.round(data.confidence * 100)}%</span>
                  </div>
                </div>
                <div className={styles.scoreStatus}>
                  {data.status === 'verified' ? (
                    <span className={styles.highConfidence}><CheckCircle size={16} /> Verified</span>
                  ) : (
                    <span className={styles.lowConfidence}><AlertTriangle size={16} /> {data.status || 'Review Needed'}</span>
                  )}
                </div>
              </div>
            </div>

            <div className={`${styles.card} glass-panel`}>
              <h2>Verification</h2>
              <div className={styles.imageComparison}>
                <div className={styles.imageBox}>
                  <span>Original</span>
                  <img src={location.state.file.preview} alt="Original" className={styles.thumbnail} />
                </div>
                {data.verificationImage && (
                  <div className={styles.imageBox}>
                    <span>Reconstructed</span>
                    <img src={data.verificationImage} alt="Verification" className={styles.thumbnail} />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Results;
