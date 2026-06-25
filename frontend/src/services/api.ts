import axios from 'axios';
import type { UploadResponse, GenerationResult, RepositorySummary, ChatMessage, ChatResponse } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 600000, // 10 min for long map-reduce generation
});

export const analyzeGitHub = async (githubUrl: string, branch = 'main'): Promise<UploadResponse> => {
  const { data } = await api.post('/repository/github', { github_url: githubUrl, branch });
  return data;
};

export const uploadRepository = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/repository/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const getRepoSummary = async (repoId: string): Promise<RepositorySummary> => {
  const { data } = await api.get(`/repository/${repoId}/summary`);
  return data;
};

export const generateRequirements = async (
  repoId: string,
  categories: string[],
  targetModules?: string[]
): Promise<GenerationResult> => {
  const { data } = await api.post(`/generate/${repoId}`, { categories, target_modules: targetModules });
  return data;
};

export const getGenerationResults = async (generationId: string): Promise<GenerationResult> => {
  const { data } = await api.get(`/generate/${generationId}/results`);
  return data;
};

export const downloadExcel = async (generationId: string): Promise<void> => {
  const response = await api.get(`/export/${generationId}/excel`, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `requirements_${generationId}.xlsx`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const downloadPdf = async (generationId: string): Promise<void> => {
  const response = await api.get(`/export/${generationId}/pdf`, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `requirements_${generationId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const downloadMarkdown = async (generationId: string): Promise<void> => {
  const response = await api.get(`/export/${generationId}/markdown`, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `requirements_${generationId}.md`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const chatWithRepo = async (repoId: string, messages: ChatMessage[]): Promise<ChatResponse> => {
  const { data } = await api.post(`/chat/${repoId}`, { messages });
  return data;
};

export default api;
