# Pineapple OFC Solver GUI User Manual

## Table of Contents
1. [Quick Start Guide](#quick-start-guide)
2. [Game Rules](#game-rules)
3. [Interface Guide](#interface-guide)
4. [Advanced Features](#advanced-features)
5. [Strategy Guide](#strategy-guide)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start Guide

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: Version 3.11 or higher
- **Memory**: 4GB RAM recommended
- **Processor**: Multi-core processor for better solving speed
- **Browser**: Latest version of Chrome, Firefox, Safari, or Edge

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/PWChenTW/PineappleSolver.git
   cd PineappleSolver
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**
   ```bash
   python -c "import streamlit; import fastapi; print('Installation successful!')"
   ```

### First Run

1. **Start the API Server** (in first terminal window)
   ```bash
   python run_api.py
   ```
   You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **Start the GUI** (in second terminal window)
   ```bash
   streamlit run gui/app_v2.py
   ```
   Your browser will automatically open http://localhost:8501

3. **Verify Connection**
   - Click "Check Connection" button in the sidebar
   - You should see "✅ API Connected Successfully"

---

## Game Rules

### Pineapple OFC Basic Rules

#### Game Objective
Arrange 13 cards into three hands and score points by comparing each hand against your opponent's.

#### Hand Structure
- **Front Hand**: 3 cards - Top row
- **Middle Hand**: 5 cards - Middle row
- **Back Hand**: 5 cards - Bottom row

#### Critical Rule
**Hand strength must follow: Back ≥ Middle ≥ Front** (Violation results in fouling)

#### Dealing Process
1. **Initial Phase**: Deal 5 cards, all must be placed
2. **Subsequent Rounds**: Deal 3 cards each round, place 2, discard 1
3. **Total 5 Rounds**: Each player places 13 cards total

### Scoring System

#### Basic Scoring
- Win each hand individually for 1 point
- Win all three hands (scoop) for 3 bonus points (6 total)
- Fouling loses all hands plus penalty points

#### Royalty Points

**Front Hand Royalties**
| Hand | Points |
|------|--------|
| 66 | 1 |
| 77 | 2 |
| 88 | 3 |
| 99 | 4 |
| TT | 5 |
| JJ | 6 |
| QQ | 7 |
| KK | 8 |
| AA | 9 |
| Trips | 10-22 |

**Middle Hand Royalties**
| Hand | Points |
|------|--------|
| Three of a Kind | 2 |
| Straight | 4 |
| Flush | 8 |
| Full House | 12 |
| Four of a Kind | 20 |
| Straight Flush | 30 |
| Royal Flush | 50 |

**Back Hand Royalties**
| Hand | Points |
|------|--------|
| Straight | 2 |
| Flush | 4 |
| Full House | 6 |
| Four of a Kind | 10 |
| Straight Flush | 15 |
| Royal Flush | 25 |

### Fantasy Land Rules

#### Entry Requirements
Achieve QQ or better in the front hand (including trips)

#### Special Treatment
Next round receive 14-15 cards at once, see all cards before placing

#### Staying Requirements
- Front: Trips
- Middle: Quads or better
- Back: Quads or better

### Joker Rules

#### Basic Rules
- Jokers can represent any card
- Automatically forms the best possible hand
- Multiple jokers can be used in the same hand

#### Usage Strategy
- Prioritize high-value hands
- Consider overall layout, not just single hands
- Be mindful of fouling risks

---

## Interface Guide

### Main Interface Layout

#### 1. Top Title Bar
Shows "🍍 OFC Solver GUI - Click Interface"

#### 2. Sidebar (Left)
- **Solver Settings**
  - Time Limit: AI thinking time (1-60 seconds)
  - Threads: Parallel computation threads (1-8)
  - Simulations: MCTS simulation count (1,000-1,000,000)
  
- **API Status**
  - Check Connection button: Verify backend service
  - Connection status indicator
  
- **Action Buttons**
  - Clear All Selections: Reset all selected cards

#### 3. Main Content Area (Two Columns)

**Left Column - Card Selector**
- **Input Target Selector**
  - Currently drawn cards
  - Player 1 hands (Front/Middle/Back)
  - Player 2 hands (Front/Middle/Back)
  
- **Card Grid**
  - Organized by suit (Spades♠, Hearts♥, Diamonds♦, Clubs♣)
  - 13 cards per suit (A-K)
  - Gray indicates used cards
  
- **Current Game State**
  - Shows selected cards for each position
  - Remove button (❌) next to each card
  - Displays current/maximum cards

**Right Column - Solution Results**
- **Solve Button**: Start AI calculation
- **Best Strategy Display**: Shows recommended placements
- **Evaluation Info**: Expected score, confidence, computation time
- **Usage Instructions**: Operation tips and shortcuts

### Operation Flow

#### 1. Select Input Mode
Choose based on current game phase:
- **Initial 5 cards**: Select "Currently drawn cards", input 5 cards
- **View opponent's cards**: Input known opponent cards
- **Analyze specific position**: Set up complete game state

#### 2. Input Cards
1. Click target position button (e.g., "Currently drawn cards")
2. Click cards in the grid to add
3. Selected cards appear in status area below
4. Click ❌ to remove mistakes

#### 3. Solve for Best Strategy
1. Confirm cards are entered correctly
2. (Optional) Adjust solver parameters in sidebar
3. Click "Solve Best Strategy" button
4. Wait for calculation (typically 5-30 seconds)

#### 4. View Results
- **Placement Recommendations**: Large icons show recommended positions
- **Expected Score**: AI's predicted average score
- **Confidence**: Reliability of recommendation
- **Calculation Details**: Simulations count, computation time

### Using AI Recommendations

#### Understanding AI Suggestions
- AI provides statistically optimal solutions based on extensive simulations
- Considers all possible future card distributions
- Balances score maximization with fouling risks

#### When to Consult AI
1. **Initial 5-card placement**: Most critical decision point
2. **Difficult choices**: Multiple seemingly equal options
3. **Learning phase**: Understanding optimal strategies through AI
4. **Verification**: Comparing your judgment with AI suggestions

#### Important Notes
- AI assumes opponents also play optimally
- Consider opponent's playing style in real games
- High-risk high-reward strategies require careful consideration

---

## Advanced Features

### Settings Explanation

#### Time Limit
- **Purpose**: Control AI thinking time
- **Recommended Values**: 
  - Quick analysis: 5-10 seconds
  - Standard analysis: 10-30 seconds
  - Deep analysis: 30-60 seconds
- **Impact**: Longer time yields more accurate results

#### Thread Count
- **Purpose**: Parallel computation acceleration
- **Recommended**: Number of CPU cores - 1
- **Note**: Too many threads may reduce efficiency

#### Simulation Count
- **Purpose**: MCTS search iterations
- **Recommended Values**:
  - Beginners: 10,000-50,000
  - Advanced: 100,000-500,000
  - Professional: 500,000+
- **Trade-off**: More simulations = better accuracy but longer time

### Save/Load Games

#### Save Current Position
1. Set up complete game state
2. Use browser bookmark feature to save URL
3. URL contains complete game information

#### Load Saved Position
1. Open saved URL
2. System automatically restores game state
3. Continue analysis or modifications

#### Export Analysis Results
- Screenshot recommended strategies
- Copy text results to notes
- Record key decision points for future reference

### Statistics Interpretation

#### Expected Score
- **Meaning**: Average score using recommended strategy
- **Reference**:
  - Positive: Advantageous position
  - Near 0: Even position
  - Negative: Disadvantageous position

#### Confidence Level
- **Meaning**: AI's certainty about recommendation
- **Interpretation**:
  - 90%+: Very certain optimal solution
  - 70-90%: Fairly reliable suggestion
  - <70%: Complex position, multiple close options

#### Win Rate Prediction
- **Meaning**: Probability estimate of winning
- **Use**: Evaluate current position strength
- **Note**: Based on both players using optimal strategy

---

## Strategy Guide

### Beginner Tips

#### 1. Basic Principles
- **Safety First**: Better conservative than fouling
- **Balanced Development**: Don't over-strengthen one hand
- **Keep Flexibility**: Maintain options early

#### 2. Common Patterns
- **Pair Distribution**: Small pairs front, big pairs middle
- **Connected Cards**: Preserve straight and flush possibilities
- **High Cards**: A, K preferably in back hand

#### 3. Risk Management
- Avoid too-strong front hand leading to foul
- Don't lock weak hands in middle too early
- Leave room for later adjustments

### Advanced Techniques

#### 1. Expected Value Thinking
- Calculate long-term value of each decision
- Consider remaining card distribution probabilities
- Balance immediate gains with future potential

#### 2. Opponent Adaptation
- Observe opponent's placement habits
- Play more aggressively against conservative opponents
- Play solidly against aggressive opponents

#### 3. Key Decision Points
- **Initial 5 cards**: Determines entire game framework
- **Cards 10-11**: Last adjustment opportunities
- **Discard choices**: Affects opponent's available cards

#### 4. Fantasy Land Strategy
- Actively pursue QQ+ in front
- Plan hand types after entering
- Balance staying conditions

### Common Mistakes to Avoid

#### 1. Over-pursuing Royalties
- **Wrong**: Ignoring foul risk for high-scoring hands
- **Right**: Ensure no fouling first, then consider royalties

#### 2. Ignoring Hand Gradient
- **Wrong**: Focus only on single hand strength
- **Right**: Maintain Back ≥ Middle ≥ Front

#### 3. Giving Up Too Early
- **Wrong**: Random placement after bad start
- **Right**: Optimize every decision

#### 4. Rigid Thinking
- **Wrong**: Fixed patterns for all situations
- **Right**: Adapt flexibly to specific cards

#### 5. Poor Time Management
- **Wrong**: Overthinking simple decisions
- **Right**: More time on key decisions, quick on simple ones

---

## Troubleshooting

### Common Issues FAQ

#### Q1: Cannot connect to API server
**Solutions**:
1. Confirm `python run_api.py` is running
2. Check if port 8000 is occupied
3. Try restarting API server
4. Check firewall settings

#### Q2: GUI won't open
**Solutions**:
1. Confirm Streamlit is properly installed
2. Check if port 8501 is available
3. Try manually opening http://localhost:8501
4. Clear browser cache

#### Q3: Solving is very slow
**Solutions**:
1. Reduce simulation count
2. Lower time limit
3. Increase thread count (if CPU supports)
4. Close other CPU-intensive programs

#### Q4: Unreasonable solving results
**Possible Causes**:
1. Incorrect game state input
2. Too few simulations
3. Used cards not properly marked

#### Q5: Interface display issues
**Solutions**:
1. Refresh browser page
2. Clear browser cache
3. Try different browser
4. Check browser console for errors

### Error Message Handling

#### "Card already used"
- **Meaning**: Attempting to select a card already placed
- **Solution**: Remove card from original position first

#### "API connection failed"
- **Meaning**: Cannot communicate with backend
- **Solution**: Ensure API server is running

#### "Solving timeout"
- **Meaning**: Computation exceeded time limit
- **Solution**: Increase time limit or reduce simulations

#### "Invalid game state"
- **Meaning**: Input violates game rules
- **Solution**: Check for duplicate cards or quantity limits

### Technical Support

#### GitHub Issues
- Repository: https://github.com/PWChenTW/PineappleSolver
- When submitting issues, include:
  - Error description
  - Steps to reproduce
  - System environment info
  - Error screenshots

#### Community Support
- Discord Group: [Coming Soon]
- Forum Discussion: [Coming Soon]

#### Developer Contact
- Author: PWChenTW
- GitHub: https://github.com/PWChenTW

### System Logs

#### View API Logs
```bash
# API server logs appear in running terminal
# Or check logs/api.log file
```

#### View GUI Logs
```bash
# Streamlit logs show in running terminal
# Browser developer tools for frontend errors
```

#### Enable Debug Mode
```bash
# API debug mode
python run_api.py --debug

# GUI debug mode
streamlit run gui/app_v2.py --logger.level=debug
```

---

## Appendix

### Keyboard Shortcuts
- **Ctrl/Cmd + R**: Refresh page
- **F5**: Reload
- **Esc**: Cancel current operation

### Terminology Reference
| English | Chinese | Description |
|---------|---------|-------------|
| Front/Top | 前墩 | 3-card hand |
| Middle | 中墩 | Middle 5-card hand |
| Back/Bottom | 後墩 | Bottom 5-card hand |
| Foul | 犯規 | Violating hand strength order |
| Royalty | 獎勵分 | Bonus points for special hands |
| Scoop | 橫掃 | Winning all three hands |
| Fantasy Land | 夢幻樂園 | Special bonus state |

### Version History
- v2.0: Click interface, optimized user experience
- v1.0: Initial version, basic functionality

---

*Last Updated: January 2025*