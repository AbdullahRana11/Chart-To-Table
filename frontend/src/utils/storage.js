// Storage utility for managing extraction history

const STORAGE_KEY = 'chart_extraction_history';

export const saveExtraction = (extraction) => {
  try {
    const history = getHistory();
    const newExtraction = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      ...extraction,
    };
    
    // Add to beginning of array (most recent first)
    history.unshift(newExtraction);
    
    // Keep only last 50 extractions
    const trimmedHistory = history.slice(0, 50);
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmedHistory));
    return newExtraction;
  } catch (error) {
    console.error('Failed to save extraction:', error);
    return null;
  }
};

export const getHistory = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Failed to get history:', error);
    return [];
  }
};

export const getExtractionById = (id) => {
  const history = getHistory();
  return history.find(item => item.id === id);
};

export const updateExtraction = (id, updates) => {
  try {
    const history = getHistory();
    const index = history.findIndex(item => item.id === id);
    
    if (index !== -1) {
      history[index] = { ...history[index], ...updates };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
      return history[index];
    }
    return null;
  } catch (error) {
    console.error('Failed to update extraction:', error);
    return null;
  }
};

export const deleteExtraction = (id) => {
  try {
    const history = getHistory();
    const filtered = history.filter(item => item.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    return true;
  } catch (error) {
    console.error('Failed to delete extraction:', error);
    return false;
  }
};

export const clearHistory = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return true;
  } catch (error) {
    console.error('Failed to clear history:', error);
    return false;
  }
};
