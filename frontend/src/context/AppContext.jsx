import React, { createContext, useState, useContext, useEffect } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [currentFile, setCurrentFile] = useState(null);
  const [extractionResult, setExtractionResult] = useState(null);
  const [history, setHistory] = useState([]);

  // Load history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('extractionHistory');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error("Failed to parse history", e);
      }
    }
  }, []);

  // Save history to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('extractionHistory', JSON.stringify(history));
  }, [history]);

  const addToHistory = (result) => {
    const newEntry = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ...result
    };
    setHistory(prev => [newEntry, ...prev]);
  };

  const clearCurrentSession = () => {
    setCurrentFile(null);
    setExtractionResult(null);
  };

  return (
    <AppContext.Provider value={{
      currentFile,
      setCurrentFile,
      extractionResult,
      setExtractionResult,
      history,
      addToHistory,
      clearCurrentSession
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
