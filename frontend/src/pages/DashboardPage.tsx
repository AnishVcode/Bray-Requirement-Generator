import { Box, Typography, Card, CardContent, Grid, Chip, Button, useTheme } from '@mui/material';
import {
  CodeRounded, FactCheckRounded, BugReportRounded, AnalyticsRounded,
  TrendingUpRounded, AutoAwesomeRounded,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAppContext } from '../App';

const MotionCard = motion(Card);

const stats = [
  { label: 'Frameworks Supported', value: '8+', icon: <CodeRounded />, color: 'primary.main' },
  { label: 'Requirement Categories', value: '7', icon: <FactCheckRounded />, color: 'primary.main' },
  { label: 'Export Formats', value: '3', icon: <TrendingUpRounded />, color: 'primary.main' },
  { label: 'AI-Powered', value: 'GPT-4o', icon: <AutoAwesomeRounded />, color: 'primary.main' },
];

const features = [
  { title: 'Functional Requirements', desc: 'Infer what the system does from source code analysis', icon: <FactCheckRounded /> },
  { title: 'API Requirements', desc: 'Extract endpoint contracts, schemas, and status codes', icon: <CodeRounded /> },
  { title: 'User Stories', desc: 'Generate As-a/I-want/So-that stories automatically', icon: <AutoAwesomeRounded /> },
  { title: 'Validation Rules', desc: 'Identify input constraints and business rules', icon: <BugReportRounded /> },
  { title: 'Edge Cases', desc: 'Discover boundary conditions and error scenarios', icon: <BugReportRounded /> },
  { title: 'Unit Test Cases', desc: 'Generate test scenarios with inputs and expected outputs', icon: <AnalyticsRounded /> },
];

export default function DashboardPage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { history } = useAppContext();

  return (
    <Box>
      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        <Box sx={{
          p: { xs: 3, md: 5 }, borderRadius: 2, mb: 4,
          background: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          position: 'relative', overflow: 'hidden',
        }}>
          <Typography variant="h3" sx={{ fontWeight: 800, mb: 1.5 }}>
            <Box component="span" color="primary.main">Requirement Generator</Box>
          </Typography>
          <Typography variant="h6" sx={{ color: 'text.secondary', mb: 3, maxWidth: 600 }}>
            AI-powered engineering assistant that analyzes repositories and generates
            comprehensive software requirements and unit test cases.
          </Typography>
          <Button
            variant="contained" size="large"
            startIcon={<AnalyticsRounded />}
            onClick={() => navigate('/analyze')}
            sx={{ px: 4, py: 1.5 }}
          >
            Analyze Repository
          </Button>
          {history.length > 0 && (
            <Chip label={`${history.length} analysis completed`} sx={{ ml: 2 }} color="secondary" variant="outlined" />
          )}
        </Box>
      </motion.div>

      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {stats.map((stat, i) => (
          <Grid item xs={6} md={3} key={stat.label}>
            <MotionCard
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * i, duration: 0.4 }}
              sx={{ textAlign: 'center', py: 2 }}
            >
              <CardContent>
                <Box sx={{ mb: 1, color: stat.color }}>{stat.icon}</Box>
                <Typography variant="h4" sx={{ fontWeight: 800, color: stat.color }}>{stat.value}</Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>{stat.label}</Typography>
              </CardContent>
            </MotionCard>
          </Grid>
        ))}
      </Grid>

      {/* Features */}
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>What Gets Generated</Typography>
      <Grid container spacing={2}>
        {features.map((feature, i) => (
          <Grid item xs={12} sm={6} md={4} key={feature.title}>
            <MotionCard
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * i + 0.4, duration: 0.4 }}
              sx={{ height: '100%' }}
            >
              <CardContent>
                <Box sx={{ color: 'primary.main', mb: 1 }}>{feature.icon}</Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>{feature.title}</Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>{feature.desc}</Typography>
              </CardContent>
            </MotionCard>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
