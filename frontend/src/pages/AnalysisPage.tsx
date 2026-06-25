import { useState, useCallback } from 'react';
import {
  Box, Typography, Card, CardContent, TextField, Button, Alert, Chip,
  LinearProgress, Stepper, Step, StepLabel, Grid, useTheme, Tabs, Tab, Divider,
  FormGroup, FormControlLabel, Checkbox,
} from '@mui/material';
import {
  GitHubIcon, UploadFileRounded, RocketLaunchRounded, CheckCircleRounded,
  CloudUploadRounded, AnalyticsRounded,
} from './icons';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../App';
import { analyzeGitHub, uploadRepository, generateRequirements, getRepoSummary } from '../services/api';
import type { RepositorySummary } from '../types';

// Icon wrapper since GitHub icon isn't in MUI default set
function GitHubSvg() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
    </svg>
  );
}

const steps = ['Input Source', 'Processing', 'Select Categories', 'Generate'];

const categoryOptions = [
  { key: 'functional', label: 'Functional Requirements', default: true },
  { key: 'non_functional', label: 'Non-Functional Requirements', default: false },
  { key: 'api', label: 'API Requirements', default: true },
  { key: 'user_story', label: 'User Stories', default: true },
  { key: 'validation_rule', label: 'Validation Rules', default: true },
  { key: 'edge_case', label: 'Edge Cases', default: true },
  { key: 'unit_test', label: 'Unit Test Cases', default: true },
];

export default function AnalysisPage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { addToHistory } = useAppContext();

  const [activeStep, setActiveStep] = useState(0);
  const [inputTab, setInputTab] = useState(0); // 0=GitHub, 1=Upload
  const [githubUrl, setGithubUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [repoId, setRepoId] = useState('');
  const [repoSummary, setRepoSummary] = useState<RepositorySummary | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [categories, setCategories] = useState<Record<string, boolean>>(
    Object.fromEntries(categoryOptions.map(c => [c.key, c.default]))
  );
  
  // Module selection state
  const [availableModules, setAvailableModules] = useState<string[]>([]);
  const [selectedModules, setSelectedModules] = useState<Record<string, boolean>>({});

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.zip')) {
      setSelectedFile(file);
    } else {
      setError('Please upload a .zip file');
    }
  }, []);

  const handleAnalyze = async () => {
    setError('');
    setLoading(true);
    setActiveStep(1);
    setStatusMessage('Processing repository...');

    try {
      let response;
      if (inputTab === 0) {
        if (!githubUrl) { setError('Please enter a GitHub URL'); setLoading(false); setActiveStep(0); return; }
        response = await analyzeGitHub(githubUrl, branch);
      } else {
        if (!selectedFile) { setError('Please select a file'); setLoading(false); setActiveStep(0); return; }
        response = await uploadRepository(selectedFile);
      }

      setRepoId(response.repo_id);
      setStatusMessage(response.message);
      
      // Fetch summary to extract modules
      try {
        const summary = await getRepoSummary(response.repo_id);
        setRepoSummary(summary);
        
        // Extract unique directories as modules
        const dirs = new Set<string>();
        summary.file_analyses?.forEach(f => {
          const parts = f.file_path.split('/');
          if (parts.length > 1) {
            dirs.add(parts.slice(0, -1).join('/'));
          } else {
            dirs.add('/'); // Root files
          }
        });
        
        const sortedDirs = Array.from(dirs).sort();
        setAvailableModules(sortedDirs);
        // By default, no modules selected (meaning "whole repo")
        setSelectedModules(Object.fromEntries(sortedDirs.map(d => [d, false])));
      } catch (err) {
        console.warn("Could not fetch summary:", err);
      }
      
      setActiveStep(2);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to process repository';
      setError(msg);
      setActiveStep(0);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setActiveStep(3);
    setStatusMessage('Generating requirements with GPT-4o...');
    setError('');

    try {
      const selectedCats = Object.entries(categories).filter(([_, v]) => v).map(([k]) => k);
      const targetModules = Object.entries(selectedModules).filter(([_, v]) => v).map(([k]) => k === '/' ? '' : k);
      
      const result = await generateRequirements(repoId, selectedCats, targetModules);
      addToHistory(result);
      navigate('/results');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Generation failed';
      setError(msg);
      setActiveStep(2);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
          <Box component="span" color="primary.main">Analyze Repository</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary', mb: 3 }}>
          Provide a GitHub URL or upload a ZIP file to generate requirements
        </Typography>
      </motion.div>

      {/* Stepper */}
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}><StepLabel>{label}</StepLabel></Step>
        ))}
      </Stepper>

      <AnimatePresence mode="wait">
        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Step 0: Input */}
      {activeStep === 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Tabs value={inputTab} onChange={(_, v) => setInputTab(v)} sx={{ mb: 3 }}>
                <Tab icon={<GitHubSvg />} iconPosition="start" label="GitHub URL" />
                <Tab icon={<CloudUploadRounded />} iconPosition="start" label="Upload ZIP" />
              </Tabs>

              {inputTab === 0 ? (
                <Box>
                  <TextField
                    fullWidth label="GitHub Repository URL" value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                    placeholder="https://github.com/username/repository"
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    label="Branch" value={branch} onChange={(e) => setBranch(e.target.value)}
                    size="small" sx={{ width: 200 }}
                  />
                </Box>
              ) : (
                <Box
                  onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}
                  sx={{
                    border: `2px dashed ${theme.palette.primary.main}`,
                    borderRadius: 3, p: 5, textAlign: 'center',
                    cursor: 'pointer', transition: 'all 0.2s',
                    bgcolor: theme.palette.mode === 'dark' ? 'rgba(124,58,237,0.05)' : 'rgba(124,58,237,0.02)',
                    '&:hover': { borderColor: 'primary.light', bgcolor: 'rgba(124,58,237,0.08)' },
                  }}
                  onClick={() => {
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.accept = '.zip';
                    input.onchange = (e) => {
                      const file = (e.target as HTMLInputElement).files?.[0];
                      if (file) setSelectedFile(file);
                    };
                    input.click();
                  }}
                >
                  <CloudUploadRounded sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                    {selectedFile ? selectedFile.name : 'Drop ZIP file here or click to browse'}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    {selectedFile ? `${(selectedFile.size / 1024 / 1024).toFixed(1)} MB` : 'Supports .zip files up to 100MB'}
                  </Typography>
                </Box>
              )}

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained" size="large"
                  startIcon={<AnalyticsRounded />}
                  onClick={handleAnalyze}
                  disabled={loading || (inputTab === 0 ? !githubUrl : !selectedFile)}
                >
                  Analyze Repository
                </Button>
              </Box>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Step 1: Processing */}
      {activeStep === 1 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Card sx={{ p: 4, textAlign: 'center' }}>
            <Box sx={{
              width: 80, height: 80, borderRadius: '50%', mx: 'auto', mb: 3,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(37, 99, 235, 0.1)',
            }}>
              <AnalyticsRounded sx={{ fontSize: 40, color: 'primary.main' }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>{statusMessage}</Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
              Cloning → Preprocessing → Parsing → Embedding → Indexing
            </Typography>
            <LinearProgress sx={{ maxWidth: 400, mx: 'auto', borderRadius: 4, height: 6 }} />
          </Card>
        </motion.div>
      )}

      {/* Step 2: Category selection */}
      {activeStep === 2 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <CheckCircleRounded sx={{ color: 'success.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>Repository Processed Successfully</Typography>
              </Box>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
                {statusMessage}
              </Typography>
              <Divider sx={{ mb: 3 }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Select requirement categories to generate:
              </Typography>
              <FormGroup>
                <Grid container spacing={1}>
                  {categoryOptions.map((cat) => (
                    <Grid item xs={12} sm={6} key={cat.key}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={categories[cat.key]}
                            onChange={(e) => setCategories(prev => ({ ...prev, [cat.key]: e.target.checked }))}
                            color="primary"
                          />
                        }
                        label={cat.label}
                      />
                    </Grid>
                  ))}
                </Grid>
              </FormGroup>

              {availableModules.length > 0 && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    Target Modules <Chip label="Optional" size="small" color="secondary" />
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                    Select specific modules to perform an exhaustive, file-by-file "Map-Reduce" generation. 
                    If none are selected, a generic fast scan over the entire codebase will be performed.
                  </Typography>
                  <Box sx={{ maxHeight: 200, overflowY: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 2, p: 2 }}>
                    <FormGroup>
                      {availableModules.map((mod) => (
                        <FormControlLabel
                          key={mod}
                          control={
                            <Checkbox
                              checked={selectedModules[mod] || false}
                              onChange={(e) => setSelectedModules(prev => ({ ...prev, [mod]: e.target.checked }))}
                              size="small"
                            />
                          }
                          label={<Typography variant="body2">{mod === '/' ? '(Root Files)' : mod}</Typography>}
                        />
                      ))}
                    </FormGroup>
                  </Box>
                </>
              )}

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained" size="large"
                  startIcon={<RocketLaunchRounded />}
                  onClick={handleGenerate}
                  disabled={loading || !Object.values(categories).some(v => v)}
                >
                  Generate Requirements
                </Button>
              </Box>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Step 3: Generating */}
      {activeStep === 3 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Card sx={{ p: 4, textAlign: 'center' }}>
            <Box sx={{
              width: 80, height: 80, borderRadius: '50%', mx: 'auto', mb: 3,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(37, 99, 235, 0.1)',
            }}>
              <RocketLaunchRounded sx={{ fontSize: 40, color: 'primary.main' }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>{statusMessage}</Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
              Retrieving code context → Generating with AI → Structuring output
            </Typography>
            <LinearProgress color="secondary" sx={{ maxWidth: 400, mx: 'auto', borderRadius: 4, height: 6 }} />
          </Card>
        </motion.div>
      )}
    </Box>
  );
}
