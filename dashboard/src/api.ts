import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export interface Agent {
  id: string;
  name: string;
  description: string;
  author: string;
  status: string;
  score_overall: number | null;
  score_reliability?: number;
  score_safety?: number;
  score_cost?: number;
  score_speed?: number;
  created_at: string;
  updated_at: string;
}

export interface EvalRecord {
  id: string;
  agent_id: string;
  score_reliability: number;
  score_cost: number;
  score_safety: number;
  score_speed: number;
  score_overall: number;
  challenges: ChallengeResult[];
  created_at: string;
}

export interface ChallengeResult {
  id: string;
  name: string;
  passed: boolean;
  score: number;
  details: string;
  duration_seconds: number;
}

export interface ChallengeSpec {
  id: string;
  name: string;
  category: string;
  difficulty: string;
  description: string;
}

export const fetchAgents = async (): Promise<Agent[]> => {
  const res = await api.get('/agents');
  return res.data.agents;
};

export const fetchAgent = async (id: string): Promise<Agent> => {
  const res = await api.get(`/agents/${id}`);
  return res.data;
};

export const fetchEvals = async (agentId: string): Promise<EvalRecord[]> => {
  const res = await api.get(`/agents/${agentId}/evals`);
  return res.data.evals;
};

export const fetchChallenges = async (): Promise<ChallengeSpec[]> => {
  const res = await api.get('/challenges');
  return res.data.challenges;
};

export const sendCoachMessage = async (agentId: string, message: string): Promise<string> => {
  const res = await api.post(`/agents/${agentId}/coach`, { message });
  return res.data.reply;
};

export default api;
