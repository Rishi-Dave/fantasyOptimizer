export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isTyping?: boolean;
}

export interface AnalysisResult {
  success: boolean;
  analysis: string;
  team_grade: string;
  brutality_score: number;
  recommendations: string[];
  confidence_score: number;
  data_sources: Record<string, boolean>;
  execution_summary: {
    steps_completed: string[];
    errors: string[];
    total_time: number;
  };
  timestamp: string;
}

export interface TradeAnalysis {
  success: boolean;
  trade_verdict: string;
  analysis: string;
  impact_score: number;
  confidence: number;
  timestamp: string;
}

export interface UserSettings {
  leagueId: string;
  username: string;
  brutalMode: boolean;
}