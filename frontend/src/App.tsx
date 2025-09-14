import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Types
interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isTyping?: boolean;
}

interface AnalysisResult {
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

interface UserSettings {
  leagueId: string;
  username: string;
  brutalMode: boolean;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Welcome to Fantasy Optimize! Configure your league settings and ask me anything about your team.',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [latestAnalysis, setLatestAnalysis] = useState<AnalysisResult | null>(null);
  const [settings, setSettings] = useState<UserSettings>({
    leagueId: '',
    username: '',
    brutalMode: true
  });
  const [tempSettings, setTempSettings] = useState<UserSettings>(settings);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    
    if (!settings.leagueId || !settings.username) {
      alert('Please configure your league settings first!');
      setShowSettings(true);
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    const typingMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      sender: 'bot',
      timestamp: new Date(),
      isTyping: true
    };

    setMessages(prev => [...prev, userMessage, typingMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Check if this is a comprehensive analysis request
      const isComprehensiveAnalysis = inputMessage.toLowerCase().includes('analyze') || 
                                     inputMessage.toLowerCase().includes('team') ||
                                     inputMessage.toLowerCase().includes('grade');

      if (isComprehensiveAnalysis) {
        const response = await axios.post(`${API_BASE_URL}/api/enhanced/analyze-team`, {
          league_id: settings.leagueId,
          username: settings.username,
          question: inputMessage,
          brutality_mode: settings.brutalMode
        });

        const result = response.data;
        setLatestAnalysis(result);
        const botResponse = `I've completed a comprehensive analysis of your team! Check out the detailed results below. Your team grade: ${result.team_grade} | Brutality Score: ${result.brutality_score}/10`;
        
        setMessages(prev => prev.slice(0, -1).concat({
          id: Date.now().toString(),
          content: botResponse,
          sender: 'bot',
          timestamp: new Date()
        }));
      } else {
        const response = await axios.post(`${API_BASE_URL}/api/enhanced/chat`, {
          league_id: settings.leagueId,
          username: settings.username,
          message: inputMessage
        });

        const result = response.data;
        setMessages(prev => prev.slice(0, -1).concat({
          id: Date.now().toString(),
          content: result.response,
          sender: 'bot',
          timestamp: new Date()
        }));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => prev.slice(0, -1).concat({
        id: Date.now().toString(),
        content: 'Sorry, I encountered an error. Please make sure the backend is running and try again.',
        sender: 'bot',
        timestamp: new Date()
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleQuickAnalysis = async (type: string, prompt: string) => {
    if (!settings.leagueId || !settings.username) {
      alert('Please configure your league settings first!');
      setShowSettings(true);
      return;
    }

    const quickMessage: Message = {
      id: Date.now().toString(),
      content: prompt,
      sender: 'user',
      timestamp: new Date()
    };

    const typingMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      sender: 'bot',
      timestamp: new Date(),
      isTyping: true
    };

    setMessages(prev => [...prev, quickMessage, typingMessage]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/enhanced/analyze-team`, {
        league_id: settings.leagueId,
        username: settings.username,
        question: prompt,
        brutality_mode: settings.brutalMode
      });

      const result = response.data;
      setLatestAnalysis(result);
      const botResponse = `${type} complete! Your team grade: ${result.team_grade} | Brutality Score: ${result.brutality_score}/10`;
      
      setMessages(prev => prev.slice(0, -1).concat({
        id: Date.now().toString(),
        content: botResponse,
        sender: 'bot',
        timestamp: new Date()
      }));
    } catch (error) {
      console.error('Error with quick analysis:', error);
      setMessages(prev => prev.slice(0, -1).concat({
        id: Date.now().toString(),
        content: 'Sorry, I encountered an error with the analysis. Please try again.',
        sender: 'bot',
        timestamp: new Date()
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = () => {
    if (!tempSettings.leagueId || !tempSettings.username) {
      alert('Please fill in both League ID and Username');
      return;
    }
    setSettings(tempSettings);
    setShowSettings(false);
    alert('Settings saved! You can now chat with the AI.');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-700 to-purple-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center">
            📈 Fantasy Optimize
          </h1>
          <p className="text-blue-200 text-lg">
            Brutally honest AI-powered fantasy football analysis
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-xl overflow-hidden">
              {/* Chat Header */}
              <div className="bg-blue-600 text-white p-4 flex justify-between items-center">
                <h2 className="text-xl font-semibold">Chat with AI Coach</h2>
                <button
                  onClick={() => setShowSettings(true)}
                  className="p-2 hover:bg-blue-700 rounded-lg transition-colors"
                  title="Settings"
                >
                  ⚙️
                </button>
              </div>

              {/* Messages */}
              <div className="h-96 overflow-y-auto p-4 bg-gray-50">
                {messages.map((message) => (
                  <div key={message.id} className={`flex items-start space-x-2 mb-4 ${message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      message.sender === 'user' ? 'bg-blue-500' : 'bg-gray-600'
                    }`}>
                      {message.sender === 'user' ? '👤' : '🤖'}
                    </div>
                    
                    <div className={`flex flex-col ${message.sender === 'user' ? 'items-end' : 'items-start'} max-w-[70%]`}>
                      <div className={`px-4 py-2 rounded-lg ${
                        message.sender === 'user' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-white text-gray-800 shadow-md'
                      }`}>
                        {message.isTyping ? (
                          <div className="flex items-center space-x-1">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                            </div>
                            <span className="text-xs text-gray-500 ml-2">Analyzing...</span>
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap">{message.content}</div>
                        )}
                      </div>
                      
                      <div className="text-xs text-gray-500 mt-1">
                        🕐 {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-4 border-t bg-white">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about your team, trades, start/sit decisions..."
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={isLoading || !inputMessage.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    ➤
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
              <button
                onClick={() => handleQuickAnalysis('Team Analysis', 'Analyze my current team and give me a grade')}
                disabled={isLoading}
                className="p-3 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left disabled:opacity-50"
              >
                <div className="font-semibold text-blue-600">Team Analysis</div>
                <div className="text-sm text-gray-600">Get a brutal grade</div>
              </button>
              <button
                onClick={() => handleQuickAnalysis('Start/Sit', 'Who should I start this week?')}
                disabled={isLoading}
                className="p-3 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left disabled:opacity-50"
              >
                <div className="font-semibold text-blue-600">Start/Sit</div>
                <div className="text-sm text-gray-600">Lineup decisions</div>
              </button>
              <button
                onClick={() => handleQuickAnalysis('Waiver Wire', 'What waiver wire pickups should I target?')}
                disabled={isLoading}
                className="p-3 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left disabled:opacity-50"
              >
                <div className="font-semibold text-blue-600">Waiver Wire</div>
                <div className="text-sm text-gray-600">Best pickups</div>
              </button>
            </div>
          </div>

          {/* Analysis Results */}
          <div className="lg:col-span-1">
            {latestAnalysis ? (
              <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between border-b pb-4">
                  <h3 className="text-lg font-semibold text-gray-800">Team Analysis</h3>
                  <div className="flex items-center space-x-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {latestAnalysis.team_grade}
                      </div>
                      <div className="text-xs text-gray-500">Grade</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold px-3 py-1 rounded-lg bg-red-50 text-red-600">
                        {latestAnalysis.brutality_score}/10
                      </div>
                      <div className="text-xs text-gray-500">Brutality</div>
                    </div>
                  </div>
                </div>

                {/* Analysis Text */}
                <div className="prose prose-sm max-w-none">
                  <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap text-sm">
                    {latestAnalysis.analysis}
                  </div>
                </div>

                {/* Recommendations */}
                {latestAnalysis.recommendations && latestAnalysis.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
                      📈 Key Recommendations
                    </h4>
                    <ul className="space-y-2">
                      {latestAnalysis.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <span className="text-green-500 mt-0.5">✓</span>
                          <span className="text-sm text-gray-700">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Data Sources */}
                <div className="border-t pt-4">
                  <span className="text-sm text-gray-500 mb-2 block">Data Sources:</span>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(latestAnalysis.data_sources).map(([source, available]) => (
                      <span
                        key={source}
                        className={`px-2 py-1 rounded-full text-xs ${
                          available 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {source.replace('_', ' ').toUpperCase()}
                        {available ? ' ✓' : ' ✗'}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-xl p-6 text-center">
                <div className="text-6xl mb-4">📊</div>
                <h3 className="text-lg font-semibold text-gray-600 mb-2">
                  No Analysis Yet
                </h3>
                <p className="text-gray-500 text-sm">
                  Ask for a team analysis to see detailed results here.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Settings Modal */}
        {showSettings && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <span>⚙️</span>
                  <h2 className="text-xl font-semibold">Settings</h2>
                </div>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sleeper League ID
                  </label>
                  <input
                    type="text"
                    value={tempSettings.leagueId}
                    onChange={(e) => setTempSettings({...tempSettings, leagueId: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter your Sleeper league ID"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Found in your Sleeper league URL: sleeper.com/leagues/LEAGUE_ID/team
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sleeper Username
                  </label>
                  <input
                    type="text"
                    value={tempSettings.username}
                    onChange={(e) => setTempSettings({...tempSettings, username: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Your Sleeper username"
                  />
                </div>

                <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className="text-red-600">⚠️</span>
                    <div>
                      <p className="font-medium text-red-800">Brutal Mode</p>
                      <p className="text-sm text-red-600">Enable brutally honest analysis</p>
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={tempSettings.brutalMode}
                      onChange={(e) => setTempSettings({...tempSettings, brutalMode: e.target.checked})}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowSettings(false)}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={saveSettings}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Save Settings
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;