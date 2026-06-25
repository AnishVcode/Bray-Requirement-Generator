import { useState } from 'react';
import {
  Box, Typography, Card, CardContent, Tabs, Tab, Chip, Button, Grid,
  useTheme, Alert, IconButton, Tooltip, Dialog, DialogTitle, DialogContent, DialogActions,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  DownloadRounded, TableChartRounded, PictureAsPdfRounded,
  DescriptionRounded, FactCheckRounded, CodeRounded,
  BugReportRounded, AnalyticsRounded, AutoAwesomeRounded,
  SecurityRounded, RuleRounded, CloseRounded, ChatRounded,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../App';
import { downloadExcel, downloadPdf, downloadMarkdown } from '../services/api';

const priorityColors: Record<string, 'error' | 'warning' | 'info' | 'default'> = {
  critical: 'error', high: 'warning', medium: 'info', low: 'default',
};

const severityColors: Record<string, 'error' | 'warning' | 'info' | 'default'> = {
  blocker: 'error', critical: 'error', major: 'warning', minor: 'info', trivial: 'default',
};

export default function ResultsPage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { currentResult } = useAppContext();
  const [tab, setTab] = useState(0);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleRowClick = (params: any) => {
    setSelectedItem(params.row);
    setDialogOpen(true);
  };

  if (!currentResult) {
    return (
      <Box sx={{ textAlign: 'center', py: 10 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>No Results Yet</Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary', mb: 3 }}>
          Analyze a repository first to see generated requirements
        </Typography>
        <Button variant="contained" onClick={() => navigate('/analyze')}>Go to Analysis</Button>
      </Box>
    );
  }

  const r = currentResult;
  const totalReqs = r.functional_requirements.length + r.api_requirements.length +
    r.non_functional_requirements.length + r.user_stories.length +
    r.validation_rules.length + r.edge_cases.length + r.test_cases.length;

  const tabs = [
    { label: `Functional (${r.functional_requirements.length})`, icon: <FactCheckRounded /> },
    { label: `API (${r.api_requirements.length})`, icon: <CodeRounded /> },
    { label: `User Stories (${r.user_stories.length})`, icon: <AutoAwesomeRounded /> },
    { label: `Validation (${r.validation_rules.length})`, icon: <RuleRounded /> },
    { label: `Edge Cases (${r.edge_cases.length})`, icon: <BugReportRounded /> },
    { label: `Unit Test Cases (${r.test_cases.length})`, icon: <AnalyticsRounded /> },
  ];

  const reqCols: GridColDef[] = [
    { field: 'requirement_id', headerName: 'ID', width: 100 },
    { field: 'module', headerName: 'Module', width: 140 },
    { field: 'description', headerName: 'Description', flex: 1, minWidth: 300 },
    { field: 'priority', headerName: 'Priority', width: 100,
      renderCell: (p) => <Chip size="small" label={p.value} color={priorityColors[p.value] || 'default'} /> },
    { field: 'severity', headerName: 'Severity', width: 100,
      renderCell: (p) => <Chip size="small" label={p.value} color={severityColors[p.value] || 'default'} variant="outlined" /> },
    { field: 'source_files', headerName: 'Source Files', width: 200,
      renderCell: (p) => (p.value as string[])?.join(', ') || '' },
  ];

  const storyCols: GridColDef[] = [
    { field: 'story_id', headerName: 'ID', width: 80 },
    { field: 'module', headerName: 'Module', width: 120 },
    { field: 'persona', headerName: 'As a...', width: 100 },
    { field: 'action', headerName: 'I want...', flex: 1, minWidth: 200 },
    { field: 'benefit', headerName: 'So that...', flex: 1, minWidth: 200 },
    { field: 'priority', headerName: 'Priority', width: 100,
      renderCell: (p) => <Chip size="small" label={p.value} color={priorityColors[p.value] || 'default'} /> },
  ];

  const validationCols: GridColDef[] = [
    { field: 'rule_id', headerName: 'ID', width: 80 },
    { field: 'module', headerName: 'Module', width: 120 },
    { field: 'field_or_parameter', headerName: 'Field', width: 130 },
    { field: 'rule_description', headerName: 'Rule', flex: 1, minWidth: 250 },
    { field: 'constraint_type', headerName: 'Type', width: 100 },
    { field: 'priority', headerName: 'Priority', width: 100,
      renderCell: (p) => <Chip size="small" label={p.value} color={priorityColors[p.value] || 'default'} /> },
  ];

  const edgeCols: GridColDef[] = [
    { field: 'edge_case_id', headerName: 'ID', width: 80 },
    { field: 'module', headerName: 'Module', width: 120 },
    { field: 'scenario', headerName: 'Scenario', width: 200 },
    { field: 'description', headerName: 'Description', flex: 1, minWidth: 200 },
    { field: 'expected_behavior', headerName: 'Expected Behavior', width: 200 },
    { field: 'severity', headerName: 'Severity', width: 100,
      renderCell: (p) => <Chip size="small" label={p.value} color={severityColors[p.value] || 'default'} /> },
  ];

  const testCols: GridColDef[] = [
    { field: 'test_id', headerName: 'ID', width: 80 },
    { field: 'module', headerName: 'Module', width: 120 },
    { field: 'scenario', headerName: 'Scenario', width: 200 },
    { field: 'test_input', headerName: 'Input', flex: 1, minWidth: 200 },
    { field: 'expected_output', headerName: 'Expected Output', flex: 1, minWidth: 200 },
    { field: 'edge_case', headerName: 'Edge', width: 70,
      renderCell: (p) => p.value ? <Chip size="small" label="Yes" color="warning" /> : '' },
    { field: 'related_requirement', headerName: 'Req', width: 80 },
  ];

  const renderGrid = () => {
    switch (tab) {
      case 0:
        return <DataGrid rows={r.functional_requirements} columns={reqCols} getRowId={(r) => r.requirement_id}
          autoHeight pageSizeOptions={[10, 25]} initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          onRowClick={handleRowClick}
          sx={{ border: 'none', '& .MuiDataGrid-cell': { borderBottom: `1px solid ${theme.palette.divider}`, cursor: 'pointer' } }} />;
      case 1:
        return <DataGrid rows={r.api_requirements} columns={reqCols} getRowId={(r) => r.requirement_id}
          autoHeight pageSizeOptions={[10, 25]} initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          onRowClick={handleRowClick}
          sx={{ border: 'none', '& .MuiDataGrid-cell': { cursor: 'pointer' } }} />;
      case 2:
        return <DataGrid rows={r.user_stories} columns={storyCols} getRowId={(r) => r.story_id}
          onRowClick={handleRowClick}
          autoHeight pageSizeOptions={[10]} sx={{ border: 'none', '& .MuiDataGrid-cell': { cursor: 'pointer' } }} />;
      case 3:
        return <DataGrid rows={r.validation_rules} columns={validationCols} getRowId={(r) => r.rule_id}
          autoHeight pageSizeOptions={[10, 25]} initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          onRowClick={handleRowClick}
          sx={{ border: 'none', '& .MuiDataGrid-cell': { cursor: 'pointer' } }} />;
      case 4:
        return <DataGrid rows={r.edge_cases} columns={edgeCols} getRowId={(r) => r.edge_case_id}
          onRowClick={handleRowClick}
          autoHeight pageSizeOptions={[10]} sx={{ border: 'none', '& .MuiDataGrid-cell': { cursor: 'pointer' } }} />;
      case 5:
        return <DataGrid rows={r.test_cases} columns={testCols} getRowId={(r) => r.test_id}
          autoHeight pageSizeOptions={[10, 25]} initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          onRowClick={handleRowClick}
          sx={{ border: 'none', '& .MuiDataGrid-cell': { cursor: 'pointer' } }} />;
      default:
        return null;
    }
  };

  return (
    <Box>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3, flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              <Box component="span" color="primary.main">Generated Requirements</Box>
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
              {r.repo_summary?.repo_name || 'Repository'} — {totalReqs} items generated in {r.processing_time_seconds}s
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button 
              variant="contained" 
              color="secondary" 
              startIcon={<ChatRounded />} 
              onClick={() => navigate(`/chat/${r.repo_id}`)}
              sx={{ mr: 2, borderRadius: 2 }}
            >
              Chat with Codebase
            </Button>
            <Tooltip title="Download Excel">
              <IconButton color="primary" onClick={() => downloadExcel(r.generation_id)}
                sx={{ bgcolor: 'action.hover' }}>
                <TableChartRounded />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download PDF">
              <IconButton color="error" onClick={() => downloadPdf(r.generation_id)}
                sx={{ bgcolor: 'action.hover' }}>
                <PictureAsPdfRounded />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download Markdown">
              <IconButton color="info" onClick={() => downloadMarkdown(r.generation_id)}
                sx={{ bgcolor: 'action.hover' }}>
                <DescriptionRounded />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Summary stats */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            { label: 'Functional', count: r.functional_requirements.length, color: 'primary.main', icon: <FactCheckRounded /> },
            { label: 'API', count: r.api_requirements.length, color: 'secondary.main', icon: <CodeRounded /> },
            { label: 'User Stories', count: r.user_stories.length, color: 'success.main', icon: <AutoAwesomeRounded /> },
            { label: 'Validation', count: r.validation_rules.length, color: 'warning.main', icon: <RuleRounded /> },
            { label: 'Edge Cases', count: r.edge_cases.length, color: 'error.main', icon: <BugReportRounded /> },
            { label: 'Unit Test Cases', count: r.test_cases.length, color: 'info.main', icon: <AnalyticsRounded /> },
          ].map((s) => (
            <Grid item xs={4} sm={2} key={s.label}>
              <Card sx={{ textAlign: 'center', py: 1 }}>
                <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Box sx={{ color: s.color, mb: 0.5 }}>{s.icon}</Box>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: s.color }}>{s.count}</Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>{s.label}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Tabs + DataGrid */}
        <Card>
          <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto"
            sx={{ borderBottom: `1px solid ${theme.palette.divider}`, px: 2, pt: 1 }}>
            {tabs.map((t, i) => (
              <Tab key={i} icon={t.icon} iconPosition="start" label={t.label} sx={{ textTransform: 'none' }} />
            ))}
          </Tabs>
          <Box sx={{ p: 2 }}>
            {renderGrid()}
          </Box>
        </Card>
      </motion.div>

      {/* Details Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        {selectedItem && (
          <>
            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {selectedItem.requirement_id || selectedItem.story_id || selectedItem.rule_id || selectedItem.edge_case_id || selectedItem.test_id} - Details
              </Typography>
              <IconButton onClick={() => setDialogOpen(false)} size="small">
                <CloseRounded />
              </IconButton>
            </DialogTitle>
            <DialogContent dividers>
              <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                  {[
                    ['Module', selectedItem.module],
                    ['Description', selectedItem.description || selectedItem.rule_description],
                    ['Scenario', selectedItem.scenario],
                    ['Persona', selectedItem.persona],
                    ['Action (I want...)', selectedItem.action],
                    ['Benefit (So that...)', selectedItem.benefit],
                    ['Field / Parameter', selectedItem.field_or_parameter],
                    ['Boundary Condition', selectedItem.boundary_condition],
                    ['Preconditions', selectedItem.preconditions],
                    ['Test Input', selectedItem.test_input],
                    ['Expected Output / Behavior', selectedItem.expected_output || selectedItem.expected_behavior],
                    ['Acceptance Criteria', selectedItem.acceptance_criteria],
                  ].map(([label, value]) => {
                    if (!value || (Array.isArray(value) && value.length === 0)) return null;
                    return (
                      <Box key={label} sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ color: 'text.secondary', mb: 0.5 }}>{label}</Typography>
                        {Array.isArray(value) ? (
                          value.map((v: string, i: number) => <Chip key={i} label={v} size="small" sx={{ mr: 1, mb: 1 }} />)
                        ) : typeof value === 'boolean' ? (
                          <Chip label={value ? 'Yes' : 'No'} size="small" color={value ? 'warning' : 'default'} />
                        ) : (
                          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>{value}</Typography>
                        )}
                      </Box>
                    );
                  })}
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card variant="outlined" sx={{ bgcolor: 'background.default' }}>
                    <CardContent>
                      <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>Attributes</Typography>
                      {selectedItem.priority && (
                        <Box sx={{ mb: 1.5, display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Priority</Typography>
                          <Chip size="small" label={selectedItem.priority} color={priorityColors[selectedItem.priority] || 'default'} />
                        </Box>
                      )}
                      {selectedItem.severity && (
                        <Box sx={{ mb: 1.5, display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Severity</Typography>
                          <Chip size="small" label={selectedItem.severity} color={severityColors[selectedItem.severity] || 'default'} variant="outlined" />
                        </Box>
                      )}
                      {selectedItem.constraint_type && (
                        <Box sx={{ mb: 1.5, display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Type</Typography>
                          <Chip size="small" label={selectedItem.constraint_type} />
                        </Box>
                      )}
                      {selectedItem.edge_case !== undefined && (
                        <Box sx={{ mb: 1.5, display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Edge Case</Typography>
                          <Chip size="small" label={selectedItem.edge_case ? 'Yes' : 'No'} color={selectedItem.edge_case ? 'warning' : 'default'} />
                        </Box>
                      )}
                      {selectedItem.related_requirement && (
                        <Box sx={{ mb: 1.5, display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Related Req</Typography>
                          <Chip size="small" label={selectedItem.related_requirement} variant="outlined" />
                        </Box>
                      )}
                      {selectedItem.source_files && selectedItem.source_files.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Source Files</Typography>
                          {selectedItem.source_files.map((f: string, i: number) => (
                            <Chip key={i} size="small" label={f} sx={{ mr: 0.5, mb: 0.5 }} variant="outlined" />
                          ))}
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions sx={{ p: 2 }}>
              <Button onClick={() => setDialogOpen(false)} variant="contained" disableElevation>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
}
