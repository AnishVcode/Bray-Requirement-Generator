import { useState } from 'react';
import {
  Box, Drawer, AppBar, Toolbar, Typography, IconButton, List, ListItem,
  ListItemIcon, ListItemText, ListItemButton, useTheme, Divider, Avatar, Chip,
} from '@mui/material';
import {
  DashboardRounded, AnalyticsRounded, HistoryRounded,
  MenuRounded, LightModeRounded, DarkModeRounded,
  CodeRounded, AutoAwesomeRounded,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';

const DRAWER_WIDTH = 260;

interface LayoutProps {
  children: React.ReactNode;
  isDark: boolean;
  toggleTheme: () => void;
}

const navItems = [
  { label: 'Dashboard', icon: <DashboardRounded />, path: '/' },
  { label: 'Analyze', icon: <AnalyticsRounded />, path: '/analyze' },
  { label: 'History', icon: <HistoryRounded />, path: '/history' },
];

export default function Layout({ children, isDark, toggleTheme }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo */}
      <Box sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Avatar sx={{
          bgcolor: 'primary.main', width: 40, height: 40,
          background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
        }}>
          <CodeRounded sx={{ fontSize: 22 }} />
        </Avatar>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 800, fontSize: '1rem', lineHeight: 1.2 }}>
            ReqGen
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
            AI Requirements Engine
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ mx: 2 }} />

      {/* Nav items */}
      <List sx={{ px: 1.5, pt: 2, flex: 1 }}>
        {navItems.map((item) => {
          const selected = location.pathname === item.path;
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                selected={selected}
                onClick={() => { navigate(item.path); setMobileOpen(false); }}
                sx={{
                  borderRadius: 2,
                  py: 1.2,
                  '&.Mui-selected': {
                    background: 'linear-gradient(135deg, rgba(124,58,237,0.15), rgba(99,102,241,0.1))',
                    '&:hover': {
                      background: 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(99,102,241,0.15))',
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: selected ? 'primary.main' : 'text.secondary' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontWeight: selected ? 600 : 400,
                    fontSize: '0.9rem',
                    color: selected ? 'primary.main' : 'text.primary',
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
        <Chip
          icon={<AutoAwesomeRounded sx={{ fontSize: 16 }} />}
          label="Powered by GPT-4o"
          size="small"
          variant="outlined"
          sx={{ fontSize: '0.7rem', width: '100%', borderColor: 'primary.main', color: 'primary.main' }}
        />
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Mobile AppBar */}
      <AppBar
        position="fixed"
        sx={{
          display: { md: 'none' },
          bgcolor: theme.palette.background.paper,
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        }}
      >
        <Toolbar>
          <IconButton edge="start" onClick={() => setMobileOpen(true)} sx={{ color: 'text.primary' }}>
            <MenuRounded />
          </IconButton>
          <Typography variant="h6" sx={{ fontWeight: 700, ml: 1, color: 'text.primary' }}>
            ReqGen
          </Typography>
          <Box sx={{ flex: 1 }} />
          <IconButton onClick={toggleTheme} sx={{ color: 'text.secondary' }}>
            {isDark ? <LightModeRounded /> : <DarkModeRounded />}
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Desktop Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          width: DRAWER_WIDTH,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            bgcolor: theme.palette.background.paper,
            borderRight: `1px solid ${theme.palette.divider}`,
          },
        }}
      >
        {drawer}
      </Drawer>

      {/* Mobile Sidebar */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { width: DRAWER_WIDTH },
        }}
      >
        {drawer}
      </Drawer>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flex: 1,
          p: { xs: 2, md: 3 },
          mt: { xs: 8, md: 0 },
          bgcolor: theme.palette.background.default,
          minHeight: '100vh',
          overflow: 'auto',
        }}
      >
        {/* Desktop top bar */}
        <Box sx={{
          display: { xs: 'none', md: 'flex' },
          justifyContent: 'flex-end',
          mb: 3,
          alignItems: 'center',
          gap: 1,
        }}>
          <IconButton onClick={toggleTheme} sx={{ color: 'text.secondary' }}>
            {isDark ? <LightModeRounded /> : <DarkModeRounded />}
          </IconButton>
          <Avatar sx={{
            width: 36, height: 36,
            background: 'linear-gradient(135deg, #7c3aed, #10b981)',
            fontSize: '0.9rem',
          }}>
            AV
          </Avatar>
        </Box>

        {children}
      </Box>
    </Box>
  );
}
