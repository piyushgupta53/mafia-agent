# 🎭 Mafia Multi-Agent Game

A fascinating real-time demonstration of AI agents playing the classic Mafia social deduction game using AutoGen (AG2) and DeepSeek LLM. Watch as AI agents with different roles, personalities, and goals interact, deceive, cooperate, and compete in this complex social scenario.

## 🌟 Features

- **Real-time Multi-Agent Gameplay**: Watch 13 AI agents play Mafia simultaneously
- **Role-based AI Personalities**: Each agent has unique behaviors based on their role:

  - 🔴 **Mafia** (3 agents): Coordinate to eliminate civilians while staying hidden
  - 🔍 **Detective** (1 agent): Investigate players to find mafia members
  - 🏥 **Doctor** (1 agent): Protect players from elimination
  - ⚪ **Civilians** (7 agents): Work together to identify and vote out mafia
  - 🟣 **Narrator** (1 agent): Facilitates game phases and announcements

- **Advanced AI Behaviors**:

  - Strategic deception and misdirection
  - Coalition building and alliance formation
  - Pattern recognition and behavioral analysis
  - Role-specific decision making

- **Real-time Web Interface**:

  - Live chat with role-specific color coding
  - Game statistics and player status
  - Vote tracking and elimination timeline
  - Phase transitions and game events

- **Powered by DeepSeek LLM**: Uses actual API calls for dynamic, unpredictable agent behavior

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- DeepSeek API key ([Get one here](https://platform.deepseek.com/))

### Installation

1. **Clone/Download the project**:

   ```bash
   git clone <repository-url>
   cd mafia-agent
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your DeepSeek API key**:

   **Option A: Using a .env file (Recommended)**

   Create a `.env` file in the project root:

   ```bash
   # Create .env file
   echo "DEEPSEEK_API_KEY=your_deepseek_api_key_here" > .env
   ```

   **Option B: Environment variable**

   ```bash
   export DEEPSEEK_API_KEY="your_deepseek_api_key_here"
   ```

   **Get your API key**: Visit [DeepSeek Platform](https://platform.deepseek.com/) to get your API key.

   ⚠️ **Security Note**: Never commit your `.env` file to version control. It's already added to `.gitignore`.

### Running the Game

**Option 1: Smart launcher with checks (Recommended)**

```bash
python run.py
```

**Option 2: Direct execution**

```bash
python main.py
```

**Option 3: Flask app directly**

```bash
cd frontend
python app.py
```

### Playing the Game

1. Open your browser to `http://localhost:5001`
2. Click **"Start New Game"** to begin
3. Watch the AI agents interact in real-time!

## 🎮 How It Works

### Game Flow

1. **Setup Phase**: 13 AI agents are assigned roles randomly
2. **First Night**: Mafia members learn each other's identities and coordinate
3. **Day Phases**:
   - Public discussion where agents share suspicions (60 seconds)
   - Voting to eliminate suspected mafia members (30 seconds)
4. **Night Phases**:
   - Mafia chooses elimination target
   - Detective investigates a player
   - Doctor protects a player
5. **Win Conditions**:
   - **Civilians win**: All mafia eliminated
   - **Mafia wins**: Mafia equals or outnumbers civilians

### AI Agent Behaviors

**🔴 Mafia Agents**:

- Coordinate privately with teammates
- Deflect suspicion through misdirection
- Vote strategically to eliminate threats
- Maintain cover as "helpful civilians"

**🔍 Detective Agent**:

- Investigate suspicious players each night
- Analyze voting patterns for inconsistencies
- Decide when to reveal findings
- Build cases against confirmed mafia

**🏥 Doctor Agent**:

- Identify valuable players to protect
- Analyze who mafia might target
- Support civilian strategy while staying hidden
- Reveal role when strategically beneficial

**⚪ Civilian Agents**:

- Form alliances with trusted players
- Track suspicious behaviors and voting patterns
- Make accusations based on evidence
- Organize group strategy against mafia

### Technical Architecture

- **Backend**: Python with AutoGen (AG2) for multi-agent orchestration
- **LLM**: DeepSeek API for dynamic agent responses
- **Frontend**: Flask + SocketIO for real-time web interface
- **Real-time Updates**: WebSocket communication for live game state
- **Threading**: Multi-threaded agent execution for concurrent interactions

## 🎯 What Makes This Fascinating

This project demonstrates several advanced AI concepts:

1. **Multi-Agent Coordination**: Watch agents form alliances and coordinate strategies
2. **Deception and Bluffing**: See how AI agents learn to lie and misdirect
3. **Social Reasoning**: Observe pattern recognition and behavioral analysis
4. **Goal-Oriented Behavior**: Agents adapt strategies based on their objectives
5. **Emergent Gameplay**: Unique interactions emerge from agent personalities

## 📊 Interface Features

### Real-time Chat

- Color-coded messages by player roles
- Filter by message type (Public, Mafia-only, Narrator)
- Automatic scrolling with manual override

### Game Statistics

- Live player status and elimination tracking
- Vote counting with visual charts
- Game progress metrics
- Timeline of key events

### Visual Indicators

- Role-specific color schemes
- Game phase transitions
- Win/loss announcements
- Connection status monitoring

## 🔒 Security

This project follows security best practices:

- **API Keys**: Never stored in code, only in environment variables
- **Environment Files**: `.env` files are automatically ignored by git
- **No Hardcoded Secrets**: All sensitive data is externalized
- **Validation**: API keys are validated on startup

### Security Checklist

- ✅ API key removed from source code
- ✅ `.env` file added to `.gitignore`
- ✅ Environment validation on startup
- ✅ Helper scripts for secure setup
- ✅ No secrets in version control

## ⚙️ Configuration

Edit `config.py` to customize:

- **Player counts** for each role
- **Game timing** (discussion/voting periods)
- **API settings** for DeepSeek
- **UI colors** and styling
- **Server configuration** (host/port)

### Current Configuration

```python
GAME_CONFIG = {
    "total_players": 13,
    "mafia_count": 3,
    "detective_count": 1,
    "doctor_count": 1,
    "civilian_count": 7,
    "discussion_time": 60,  # seconds
    "voting_time": 30,  # seconds
    "max_discussion_rounds": 6,
    "response_timeout": 15,  # seconds
}

FLASK_CONFIG = {"host": "0.0.0.0", "port": 5001, "debug": True}
```

## 🔧 Troubleshooting

**Game won't start**:

- Check your DeepSeek API key is set correctly
- Ensure all dependencies are installed
- Check console for error messages
- Run `python test_env.py` to verify your setup

**Agents not responding**:

- Verify API key has sufficient credits
- Check network connectivity
- Look for rate limiting messages

**Environment setup issues**:

- Run `python test_env.py` to verify configuration
- Ensure `.env` file is in the project root directory
- Check that API key starts with "sk-"

**Frontend not loading**:

- Make sure Flask server is running on port 5001
- Clear browser cache
- Check for JavaScript errors in browser console

## 🧪 Experiment Ideas

Try modifying the game to explore different scenarios:

1. **Personality Variations**: Edit agent personalities in the role classes
2. **Role Balance**: Adjust the number of each role type in `config.py`
3. **Communication Patterns**: Modify how agents share information
4. **Decision Making**: Alter voting and action strategies
5. **Game Rules**: Implement variant rules or new roles

## 📝 Project Structure

```
mafia-agent/
├── requirements.txt          # Python dependencies
├── config.py                # Game configuration
├── main.py                  # Main entry point
├── run.py                   # Smart launcher with checks
├── test_env.py              # Environment testing script
├── game/                    # Core game logic
│   ├── game_controller.py   # Main game orchestration
│   ├── game_state.py        # State management
│   ├── utils.py             # Utility functions
│   └── agents/              # AI agent implementations
│       ├── base_agent.py    # Base agent class
│       ├── mafia_agent.py   # Mafia role agent
│       ├── detective_agent.py # Detective role agent
│       ├── doctor_agent.py  # Doctor role agent
│       ├── civilian_agent.py # Civilian role agent
│       └── narrator_agent.py # Game narrator
└── frontend/                # Web interface
    ├── app.py              # Flask application
    ├── templates/          # HTML templates
    └── static/             # CSS and JavaScript
```

## 🤝 Contributing

This project demonstrates advanced AI agent interactions. Feel free to:

- Experiment with different agent strategies
- Add new roles or game mechanics
- Improve the visual interface
- Optimize agent decision-making algorithms

## 📄 License

This project is for educational and research purposes, demonstrating multi-agent AI systems and social game theory.

---

**🎭 Watch AI agents master the art of deception in real-time! 🎭**
