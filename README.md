# Fantasy Optimize 🏈

A brutally honest AI-powered fantasy football analysis system built with React and FastAPI, integrated with the Sleeper API for real-time league data.

## Features

- 🤖 **AI-Powered Analysis**: Get intelligent fantasy football advice
- 🔥 **Brutal Honesty Mode**: Unfiltered, harsh team analysis 
- 📊 **Real Data Integration**: Uses Sleeper API for actual league data
- 💬 **Interactive Chat**: Ask questions about your team, trades, start/sit decisions
- 📈 **Detailed Analytics**: Team grades, brutality scores, and recommendations
- ⚡ **Quick Actions**: One-click team analysis, waiver wire suggestions, and lineup advice

## Project Structure

```
fantasy-optimize/
├── server.py           # FastAPI backend server
├── frontend/           # React frontend application
│   ├── src/
│   │   ├── App.tsx                    # Main React application
│   │   ├── components/                # React components
│   │   │   ├── ChatMessage.tsx        # Chat message display
│   │   │   ├── SettingsModal.tsx      # League settings modal
│   │   │   └── AnalysisResult.tsx     # Analysis results panel
│   │   ├── services/
│   │   │   └── api.ts                 # API client
│   │   └── types/
│   │       └── fantasy.ts             # TypeScript interfaces
├── requirements.txt    # Python dependencies
├── run.py             # Quick start script
├── .env               # Environment variables (API keys)
└── README.md          # This file
```

## Technology Stack

- **Frontend**: React 19, TypeScript, Tailwind CSS, Axios
- **Backend**: FastAPI, Python 3.8+, Pydantic
- **APIs**: Sleeper API, OpenAI API (optional)
- **Build Tools**: Vite, Node.js

## Quick Start

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the backend server
python run.py
# OR
python server.py
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 3. Configure Your League

1. Open the frontend in your browser
2. Click the ⚙️ settings icon
3. Enter your:
   - **Sleeper League ID** (found in your league URL)
   - **Sleeper Username**
   - **Brutal Mode** preference

### 4. Start Analyzing!

Ask questions like:
- "Analyze my current team and give me a grade"
- "Who should I start this week?"
- "What waiver wire pickups should I target?"
- "Should I make this trade?"

## API Integration

### Sleeper API
- Fetches real league data, rosters, and player information
- No API key required for basic functionality

### OpenAI (Optional)
- Add `OPENAI_API_KEY` to `.env` for enhanced AI responses
- Falls back to smart contextual responses if not configured

## Environment Variables

Create a `.env` file in the root directory:

```bash
# Optional: Enhanced AI responses
OPENAI_API_KEY=your_openai_api_key_here

# Your league info for quick testing
LEAGUE_ID=your_sleeper_league_id
USERNAME=your_sleeper_username
```

## Features Overview

### Team Analysis
- **Team Grade**: A-F scale based on roster strength
- **Brutality Score**: 1-10 scale of analysis harshness
- **Recommendations**: Actionable advice for improvement
- **Data Sources**: Shows which APIs were used for analysis

### Chat Interface
- **Contextual Responses**: AI understands different question types
- **Real Data**: Uses your actual roster and league settings
- **Multiple Analysis Types**: Team, start/sit, waiver wire, trades
- **Typing Indicators**: Real-time chat experience

### Quick Actions
- **Team Analysis**: One-click comprehensive team review
- **Start/Sit**: Weekly lineup decision help
- **Waiver Wire**: Best available player recommendations

## Development

### Frontend Development
```bash
cd frontend
npm run dev    # Development server
npm run build  # Production build
npm run lint   # Code linting
```

### Backend Development
```bash
python server.py    # Start development server
# Server runs with hot reload enabled
```

## License

MIT License - Feel free to use this project for your fantasy football domination! 🏆