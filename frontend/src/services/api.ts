import axios from 'axios';
import { AnalysisResult, TradeAnalysis } from '../types/fantasy';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds for analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

export class FantasyAPI {
  static async analyzeTeam(
    leagueId: string, 
    username: string, 
    question?: string, 
    brutalMode = true
  ): Promise<AnalysisResult> {
    const response = await api.post('/enhanced/analyze-team', {
      league_id: leagueId,
      username: username,
      question: question || "Provide a comprehensive analysis of my fantasy team",
      brutality_mode: brutalMode
    });
    
    return response.data;
  }

  static async analyzeTrade(
    leagueId: string,
    username: string,
    tradeDetails: any
  ): Promise<TradeAnalysis> {
    const response = await api.post('/enhanced/analyze-trade', {
      league_id: leagueId,
      username: username,
      trade_details: tradeDetails
    });
    
    return response.data;
  }

  static async quickAnalysis(
    leagueId: string,
    username: string,
    analysisType: string
  ): Promise<{ success: boolean; quick_analysis: string; key_points: string[] }> {
    const response = await api.post('/enhanced/quick-analysis', {
      league_id: leagueId,
      username: username,
      analysis_type: analysisType
    });
    
    return response.data;
  }

  static async chat(
    leagueId: string,
    username: string,
    message: string
  ): Promise<{ success: boolean; response: string; analysis_type: string; confidence: number }> {
    const response = await api.post('/enhanced/chat', {
      league_id: leagueId,
      username: username,
      message: message
    });
    
    return response.data;
  }

  static async getWorkflowStatus(): Promise<any> {
    const response = await api.get('/enhanced/workflow-status');
    return response.data;
  }

  static async getAvailableLLMs(): Promise<any> {
    const response = await api.get('/enhanced/available-llms');
    return response.data;
  }

  static async healthCheck(): Promise<any> {
    const response = await api.get('/enhanced/health');
    return response.data;
  }

  // Sleeper API endpoints
  static async getLeagueInfo(leagueId: string): Promise<any> {
    const response = await api.get(`/sleeper/league/${leagueId}`);
    return response.data;
  }

  static async getUserRoster(leagueId: string, username: string): Promise<any> {
    const response = await api.post('/sleeper/user-roster', {
      league_id: leagueId,
      username: username
    });
    return response.data;
  }
}