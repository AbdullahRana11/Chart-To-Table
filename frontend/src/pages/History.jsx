import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { History as HistoryIcon, Trash2, Eye, Calendar, TrendingUp } from 'lucide-react';
import { getHistory, clearHistory, deleteExtraction } from '../utils/storage';
import styles from './History.module.css';

const History = () => {
  const [history, setHistory] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = () => {
    const data = getHistory();
    setHistory(data);
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to clear all history?')) {
      clearHistory();
      setHistory([]);
    }
  };

  const handleDelete = (id, e) => {
    e.stopPropagation();
    if (window.confirm('Delete this extraction?')) {
      deleteExtraction(id);
      loadHistory();
    }
  };

  const handleView = (item) => {
    // Navigate to results with saved data
    navigate('/results', { 
      state: { 
        savedData: item,
        file: { name: item.filename, preview: item.thumbnail }
      } 
    });
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="container">
      <motion.div 
        className={styles.historyWrapper}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className={styles.header}>
          <div>
            <h1 className="text-gradient">
              <HistoryIcon size={32} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
              Extraction History
            </h1>
            <p>View and manage your past chart extractions</p>
          </div>
          {history.length > 0 && (
            <button onClick={handleClearAll} className={styles.clearBtn}>
              <Trash2 size={18} />
              Clear All
            </button>
          )}
        </div>

        {history.length === 0 ? (
          <div className={styles.emptyState}>
            <HistoryIcon size={64} opacity={0.3} />
            <h2>No Extraction History</h2>
            <p>Start by uploading and extracting chart data</p>
            <button 
              className="btn-primary" 
              onClick={() => navigate('/upload')}
              style={{ marginTop: '1rem' }}
            >
              Upload Chart
            </button>
          </div>
        ) : (
          <div className={styles.grid}>
            {history.map((item, index) => (
              <motion.div
                key={item.id}
                className={`${styles.card} glass-panel`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => handleView(item)}
              >
                {item.thumbnail && (
                  <div className={styles.thumbnail}>
                    <img src={item.thumbnail} alt={item.filename} />
                  </div>
                )}
                
                <div className={styles.content}>
                  <h3 className={styles.filename}>{item.filename}</h3>
                  
                  <div className={styles.meta}>
                    <span className={styles.date}>
                      <Calendar size={14} />
                      {formatDate(item.timestamp)}
                    </span>
                    <span className={styles.confidence}>
                      <TrendingUp size={14} />
                      {Math.round(item.confidence * 100)}% confidence
                    </span>
                  </div>

                  <div className={styles.stats}>
                    <div className={styles.stat}>
                      <span className={styles.statLabel}>Rows</span>
                      <span className={styles.statValue}>{item.rows?.length || 0}</span>
                    </div>
                    <div className={styles.stat}>
                      <span className={styles.statLabel}>Columns</span>
                      <span className={styles.statValue}>{item.headers?.length || 0}</span>
                    </div>
                  </div>
                </div>

                <div className={styles.actions}>
                  <button 
                    className={styles.viewBtn}
                    onClick={() => handleView(item)}
                  >
                    <Eye size={16} />
                    View
                  </button>
                  <button 
                    className={styles.deleteBtn}
                    onClick={(e) => handleDelete(item.id, e)}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default History;
