import { useState, useMemo, createContext, useContext, useEffect } from 'react';
import localforage from 'localforage';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { lightTheme, darkTheme } from './theme/theme';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import AnalysisPage from './pages/AnalysisPage';
import ResultsPage from './pages/ResultsPage';
import HistoryPage from './pages/HistoryPage';
import ChatPage from './pages/ChatPage';
import type { GenerationResult } from './types';
import './index.css';

// ─── App Context ───
interface AppContextType {
  currentResult: GenerationResult | null;
  setCurrentResult: (r: GenerationResult | null) => void;
  history: GenerationResult[];
  addToHistory: (r: GenerationResult) => void;
  removeFromHistory: (id: string) => void;
}

export const AppContext = createContext<AppContextType>({
  currentResult: null,
  setCurrentResult: () => {},
  history: [],
  addToHistory: () => {},
  removeFromHistory: () => {},
});

export const useAppContext = () => useContext(AppContext);

function App() {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('reqgen_theme');
    return saved === 'dark';
  });

  const toggleTheme = () => {
    setIsDark((prev) => {
      const next = !prev;
      localStorage.setItem('reqgen_theme', next ? 'dark' : 'light');
      return next;
    });
  };

  const theme = useMemo(() => (isDark ? darkTheme : lightTheme), [isDark]);

  const [currentResult, setCurrentResult] = useState<GenerationResult | null>(null);
  const [history, setHistory] = useState<GenerationResult[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const savedHistory = await localforage.getItem<GenerationResult[]>('reqgen_history');
        if (savedHistory) setHistory(savedHistory);
        
        const savedResult = await localforage.getItem<GenerationResult>('reqgen_current_result');
        if (savedResult) setCurrentResult(savedResult);
      } catch (e) {
        console.error("Failed to load data from storage", e);
      } finally {
        setIsLoaded(true);
      }
    }
    loadData();
  }, []);

  useEffect(() => {
    if (isLoaded) {
      localforage.setItem('reqgen_history', history).catch(console.error);
    }
  }, [history, isLoaded]);

  useEffect(() => {
    if (isLoaded) {
      if (currentResult) {
        localforage.setItem('reqgen_current_result', currentResult).catch(console.error);
      } else {
        localforage.removeItem('reqgen_current_result').catch(console.error);
      }
    }
  }, [currentResult, isLoaded]);

  const addToHistory = (r: GenerationResult) => {
    setHistory((prev) => [r, ...prev]);
    setCurrentResult(r);
  };

  const removeFromHistory = (id: string) => {
    setHistory((prev) => prev.filter((item) => item.generation_id !== id));
    if (currentResult?.generation_id === id) {
      setCurrentResult(null);
    }
  };

  return (
    <AppContext.Provider value={{ currentResult, setCurrentResult, history, addToHistory, removeFromHistory }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <Layout isDark={isDark} toggleTheme={toggleTheme}>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/analyze" element={<AnalysisPage />} />
              <Route path="/results" element={<ResultsPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/chat/:repoId" element={<ChatPage />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ThemeProvider>
    </AppContext.Provider>
  );
}

export default App;
