import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, TextField, IconButton, Paper, Avatar, CircularProgress, Card,
  Divider, Tooltip
} from '@mui/material';
import { SendRounded, PersonRounded, SmartToyRounded, ArrowBackRounded } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { chatWithRepo } from '../services/api';
import type { ChatMessage, ChatResponse } from '../types';

export default function ChatPage() {
  const { repoId } = useParams<{ repoId: string }>();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || !repoId) return;

    const userMsg: ChatMessage = { role: 'user', content: input.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await chatWithRepo(repoId, newMessages);
      setMessages([...newMessages, response.message]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages([...newMessages, { role: 'assistant', content: 'Sorry, I encountered an error while processing your request.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <IconButton onClick={() => navigate('/results')} sx={{ mr: 2 }}>
          <ArrowBackRounded />
        </IconButton>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          <Box component="span" color="primary.main">Chat with Codebase</Box>
        </Typography>
      </Box>

      <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRadius: 3, border: '1px solid', borderColor: 'divider' }} elevation={0}>
        <Box sx={{ flex: 1, overflowY: 'auto', p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {messages.length === 0 && (
            <Box sx={{ m: 'auto', textAlign: 'center', color: 'text.secondary' }}>
              <SmartToyRounded sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6">How can I help you with this repository?</Typography>
              <Typography variant="body2">Ask me to explain code, find functions, or describe architectures.</Typography>
            </Box>
          )}

          {messages.map((msg, idx) => (
            <Box key={idx} sx={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <Box sx={{ display: 'flex', gap: 2, maxWidth: '80%', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
                <Avatar sx={{ bgcolor: msg.role === 'user' ? 'primary.main' : 'secondary.main', width: 32, height: 32 }}>
                  {msg.role === 'user' ? <PersonRounded fontSize="small" /> : <SmartToyRounded fontSize="small" />}
                </Avatar>
                <Paper sx={{
                  p: 2,
                  bgcolor: msg.role === 'user' ? 'primary.main' : 'background.paper',
                  color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                  borderRadius: 2,
                  border: msg.role === 'assistant' ? '1px solid' : 'none',
                  borderColor: 'divider',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: msg.content.includes('```') ? 'monospace' : 'inherit'
                }} elevation={msg.role === 'user' ? 2 : 0}>
                  {msg.content}
                </Paper>
              </Box>
            </Box>
          ))}
          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                  <SmartToyRounded fontSize="small" />
                </Avatar>
                <Paper sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 2, border: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center' }}>
                  <CircularProgress size={20} color="inherit" />
                </Paper>
              </Box>
            </Box>
          )}
          <div ref={messagesEndRef} />
        </Box>

        <Divider />

        <Box sx={{ p: 2, bgcolor: 'background.paper' }}>
          <TextField
            fullWidth
            placeholder="Ask something about the codebase..."
            variant="outlined"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            multiline
            maxRows={4}
            InputProps={{
              endAdornment: (
                <IconButton color="primary" onClick={handleSend} disabled={!input.trim() || isLoading}>
                  <SendRounded />
                </IconButton>
              ),
              sx: { borderRadius: 3, bgcolor: 'background.default' }
            }}
          />
        </Box>
      </Paper>
    </Box>
  );
}
