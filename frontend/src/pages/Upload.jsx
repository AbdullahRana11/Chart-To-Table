import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload as UploadIcon, File, X, ArrowRight, AlertCircle } from 'lucide-react';
import styles from './Upload.module.css';

const Upload = () => {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    validateAndSetFile(droppedFile);
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (file) => {
    setError('');
    if (!file) return;

    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a valid image file (JPG, PNG).');
      return;
    }

    setFile(Object.assign(file, {
      preview: URL.createObjectURL(file)
    }));
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleExtract = () => {
    if (!file) return;
    // Simulate extraction process
    navigate('/results', { state: { file } });
  };

  return (
    <div className="container">
      <motion.div 
        className={styles.uploadWrapper}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className={styles.header}>
          <h1 className="text-gradient">Upload Chart Image</h1>
          <p>Drag and drop your chart image here, or click to browse.</p>
        </div>

        <div 
          className={`${styles.dropzone} ${isDragging ? styles.dragging : ''} ${error ? styles.error : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept="image/png, image/jpeg, image/jpg"
            hidden 
          />
          
          <AnimatePresence mode="wait">
            {!file ? (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className={styles.placeholder}
              >
                <div className={styles.iconCircle}>
                  <UploadIcon size={32} />
                </div>
                <p className={styles.dropText}>Drop image here</p>
                <span className={styles.browseText}>or click to browse</span>
              </motion.div>
            ) : (
              <motion.div 
                key="preview"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={styles.previewContainer}
                onClick={(e) => e.stopPropagation()}
              >
                <img src={file.preview} alt="Preview" className={styles.previewImage} />
                <div className={styles.fileInfo}>
                  <File size={16} />
                  <span>{file.name}</span>
                  <button onClick={removeFile} className={styles.removeBtn}>
                    <X size={16} />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {error && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className={styles.errorMessage}
          >
            <AlertCircle size={16} />
            {error}
          </motion.div>
        )}

        <div className={styles.actions}>
          <button 
            className={`btn-primary ${styles.extractBtn}`}
            disabled={!file}
            onClick={handleExtract}
          >
            Extract Data <ArrowRight size={18} />
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default Upload;
