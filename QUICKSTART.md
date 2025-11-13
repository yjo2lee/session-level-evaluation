# Quick Start Guide

## Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test the setup:**
   ```bash
   python test_setup.py
   ```
   You should see "✓ ALL TESTS PASSED!"

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```
   The app will open in your browser at `http://localhost:8501`

## Using the System

### For Annotators

#### Initial Setup
1. Enter your User ID (e.g., "annotator_01")
2. Click "Let's start the chat!"
3. Choose annotation mode:
   - **Turn-by-turn**: Compare responses at each turn, then have full conversations
   - **Whole conversation with two assistants**: Have full conversations only

#### Turn-by-Turn Mode
1. Type your question
2. Two responses appear side-by-side
3. Click "Select" on your preferred response
4. The selected response is highlighted in green
5. Continue the conversation
6. Click "Complete and Next Chat" when done (or after 10 turns)

#### Session-Level Mode
1. Have a full conversation with Assistant A
2. Click "Complete and Next Chat" when satisfied
3. Write notes about the conversation
4. Repeat with Assistant B
5. Choose which overall conversation was better

### For Administrators

#### Accessing the Dashboard
1. On the guide page, check "Show admin options"
2. Enter password: `admin123`
3. Click "Access Summary Page"

#### Viewing Annotations
1. Select a User ID from the dropdown
2. Select a Query to view
3. Review:
   - Turn-level selection ratios (how often each model was chosen)
   - Session-level notes and preferences
   - Consistency between turn and session preferences
   - Aggregate statistics across all queries

## Tips

- **First message is important**: Your first message in the first session becomes the default starting query for subsequent sessions
- **End early if satisfied**: You don't need to use all 10 turns - click "Complete and Next Chat" whenever ready
- **Natural interaction**: The interface is designed to feel like a normal chat to avoid bias
- **Take your time**: There's no time limit - provide thoughtful evaluations


## Next Steps

### Customizing the Interface

- **Change max turns**: Search for `>= 10` in [app.py](app.py)
- **Modify styling**: Edit the CSS section at the top of [app.py](app.py)
- **Change admin password**: Find `admin123` in [app.py](app.py) and replace it

### Exporting Data

To export your annotations:
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('annotation_system.db')
turn_data = pd.read_sql_query("SELECT * FROM turn_level_turns", conn)
session_data = pd.read_sql_query("SELECT * FROM session_level_turns", conn)
turn_data.to_csv('turn_annotations.csv')
session_data.to_csv('session_annotations.csv')
```

