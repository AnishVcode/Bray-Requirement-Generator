/**
 * Material UI theme configuration with dark/light mode support.
 * Code-editor-inspired premium design with violet-blue gradients.
 */
import { createTheme, ThemeOptions } from '@mui/material/styles';

const commonOptions: ThemeOptions = {
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica Neue", sans-serif',
    h1: { fontWeight: 800, letterSpacing: '-0.02em' },
    h2: { fontWeight: 700, letterSpacing: '-0.01em' },
    h3: { fontWeight: 700 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { fontWeight: 600, textTransform: 'none' as const },
  },
  shape: { borderRadius: 6 },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          padding: '8px 20px',
          fontSize: '0.9rem',
          boxShadow: 'none',
          '&:hover': { boxShadow: 'none' },
        },
        containedPrimary: ({ theme }) => ({
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
          color: '#fff',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: `0 6px 16px ${theme.palette.mode === 'dark' ? 'rgba(59, 130, 246, 0.4)' : 'rgba(37, 99, 235, 0.3)'}`,
            background: `linear-gradient(135deg, ${theme.palette.primary.light} 0%, ${theme.palette.primary.main} 100%)`,
          },
        }),
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: 'none',
          border: '1px solid var(--mui-palette-divider)',
          transition: 'none',
          '&:hover': {
            transform: 'none',
            boxShadow: 'none',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 500, borderRadius: 6 },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { borderRadius: 8 },
      },
    },
  },
};

export const lightTheme = createTheme({
  ...commonOptions,
  palette: {
    mode: 'light',
    primary: { main: '#2563eb', light: '#3b82f6', dark: '#1d4ed8' },
    secondary: { main: '#0ea5e9', light: '#38bdf8', dark: '#0284c7' },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    text: {
      primary: '#0f172a',
      secondary: '#475569',
    },
    success: { main: '#10b981' },
    warning: { main: '#f59e0b' },
    error: { main: '#ef4444' },
    info: { main: '#3b82f6' },
    divider: '#e2e8f0',
  },
});

export const darkTheme = createTheme({
  ...commonOptions,
  palette: {
    mode: 'dark',
    primary: { main: '#3b82f6', light: '#60a5fa', dark: '#2563eb' },
    secondary: { main: '#38bdf8', light: '#7dd3fc', dark: '#0ea5e9' },
    background: {
      default: '#020617',
      paper: '#0f172a',
    },
    text: {
      primary: '#f8fafc',
      secondary: '#94a3b8',
    },
    success: { main: '#10b981' },
    warning: { main: '#fbbf24' },
    error: { main: '#f87171' },
    info: { main: '#3b82f6' },
    divider: '#1e293b',
  },
});
