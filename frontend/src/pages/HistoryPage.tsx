import {
  Box, Typography, Card, CardContent, Chip, Button, useTheme, IconButton
} from '@mui/material';
import {
  HistoryRounded, AnalyticsRounded, AccessTimeRounded, DeleteRounded
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../App';

export default function HistoryPage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { history, setCurrentResult, removeFromHistory } = useAppContext();

  if (history.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 10 }}>
        <HistoryRounded sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>No Analysis History</Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary', mb: 3 }}>
          Your previous analysis results will appear here
        </Typography>
        <Button variant="contained" onClick={() => navigate('/analyze')}>Start Analysis</Button>
      </Box>
    );
  }

  return (
    <Box>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 3 }}>
          <Box component="span" color="primary.main">Analysis History</Box>
        </Typography>
      </motion.div>

      {history.map((result, index) => {
        const total = result.functional_requirements.length + result.api_requirements.length +
          result.user_stories.length + result.validation_rules.length +
          result.edge_cases.length + result.test_cases.length;

        return (
          <motion.div
            key={result.generation_id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card sx={{ mb: 2, cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }}
              onClick={() => { setCurrentResult(result); navigate('/results'); }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                <Box sx={{
                  width: 48, height: 48, borderRadius: 2, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  background: 'rgba(37, 99, 235, 0.1)',
                }}>
                  <AnalyticsRounded sx={{ color: 'primary.main' }} />
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    {result.repo_summary?.repo_name || 'Repository'}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <AccessTimeRounded sx={{ fontSize: 14 }} />
                    {new Date(result.created_at).toLocaleString()} · {result.processing_time_seconds}s
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                  <Chip label={`${total} items`} size="small" color="primary" variant="outlined" />
                  <Chip label={result.status} size="small" color={result.status === 'completed' ? 'success' : 'default'} />
                  {result.repo_summary?.detected_frameworks?.map((fw) => (
                    <Chip key={fw} label={fw} size="small" variant="outlined" />
                  ))}
                  <IconButton
                    size="small"
                    color="error"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFromHistory(result.generation_id);
                    }}
                  >
                    <DeleteRounded fontSize="small" />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </Box>
  );
}
