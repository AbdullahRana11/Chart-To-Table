import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Clock, ArrowRight, FileText, Calendar } from 'lucide-react';
import { useApp } from '../context/AppContext';
import styles from './History.module.css';

const History = () => {
  const { history, setExtractionResult, setCurrentFile } = useApp();
  const navigate = useNavigate();

  const handleViewResult = (item) => {
    // Restore state from history item
    setExtractionResult(item);
    // We might not have the original file object for preview if it was from a previous session
    // but we can try to use what we have or just show the data
    setCurrentFile({ name: item.title, preview: null }); 
    navigate('/results');
  };

  return (
    <div className="container">
      <motion.div 
        className={styles.historyWrapper}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className={styles.header}>
          <h1>Extraction History</h1>
          <p>View your past chart extractions.</p>
        </div>

        {history.length === 0 ? (
          <div className={styles.emptyState}>
            <Clock size={48} className={styles.emptyIcon} />
            <h3>No History Yet</h3>
            <p>Upload a chart to see it here.</p>
            <button onClick={() => navigate('/upload')} className="btn-primary">
              Start Extraction
            </button>
          </div>
        ) : (
          <div className={styles.grid}>
            {history.map((item) => (
              <motion.div 
                key={item.id}
                className={`${styles.card} glass-panel`}
                whileHover={{ y: -5 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <div className={styles.cardHeader}>
                  <div className={styles.iconBox}>
                    <FileText size={20} />
                  </div>
                  <span className={styles.confidence} style={{ 
                    color: item.confidence > 80 ? '#4ade80' : '#fbbf24' 
                  }}>
                    {Math.round(item.confidence)}% Acc
                  </span>
                </div>
                
                <h3>{item.title || 'Untitled Extraction'}</h3>
                
                <div className={styles.meta}>
                  <div className={styles.metaItem}>
                    <Calendar size={14} />
                    <span>{new Date(item.timestamp).toLocaleDateString()}</span>
                  </div>
                  <div className={styles.metaItem}>
                    <Clock size={14} />
                    <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                <button 
                  className={styles.viewBtn}
                  onClick={() => handleViewResult(item)}
                >
                  View Results <ArrowRight size={16} />
                </button>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default History;
