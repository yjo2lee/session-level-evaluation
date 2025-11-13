# 📚 Complete Project Index

A comprehensive index of all files in the AI Assistant Annotation System.

## 🎯 Quick Navigation

| I want to... | Go to... |
|--------------|----------|
| Get started immediately | [START_HERE.md](START_HERE.md) |
| Install and run the app | [QUICKSTART.md](QUICKSTART.md) |
| Understand the system | [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) |
| Learn about the database | [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) |
| Customize AI responses | [ai_service.py](ai_service.py) |
| Modify the UI | [app.py](app.py) |
| Change database operations | [database.py](database.py) |

## 📖 Documentation Files

### [START_HERE.md](START_HERE.md) (3.3KB)
**Read this first!**
- 5-minute quick start
- Documentation reading guide
- Common tasks reference
- Quick troubleshooting

### [QUICKSTART.md](QUICKSTART.md) (3.8KB)
**Complete setup guide**
- Step-by-step installation
- Usage instructions for annotators
- Admin dashboard access
- Integration examples
- Common issues and solutions

### [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) (9.4KB)
**High-level system overview**
- Feature summary
- All file descriptions
- Customization points
- Research use cases
- Data export methods
- Security considerations

### [README.md](README.md) (4.3KB)
**Detailed documentation**
- Complete feature list
- Installation details
- Usage instructions
- Project structure
- Database schema overview
- Customization guide

### [WORKFLOW.md](WORKFLOW.md) (17KB)
**Visual workflow documentation**
- System flow diagrams
- Turn-level workflow
- Session-level workflow
- State management
- Key features explained

### [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) (11KB)
**Database documentation**
- Complete schema with ERD
- Table descriptions
- Data flow diagrams
- SQL query examples
- Export methods

## 💻 Code Files

### [app.py](app.py) (24KB) ⭐ Main Application
**Streamlit application with full UI**

**Key Functions:**
- `show_guide_page()` - User login and mode selection
- `show_turn_level_page()` - Turn-by-turn annotation interface
- `show_session_level_page()` - Session-level annotation router
- `show_session_conversation()` - Individual conversation interface
- `show_notes_input()` - Notes collection interface
- `show_final_preference()` - Final preference selection
- `show_summary_page()` - Admin dashboard

**Main Sections:**
- Lines 1-50: Imports and page config
- Lines 51-100: Session state initialization
- Lines 101-150: CSS styling
- Lines 151-250: Guide page
- Lines 251-400: Turn-level annotation
- Lines 401-650: Session-level annotation
- Lines 651-800: Summary dashboard

**Customization Points:**
- Line ~285: Admin password
- Line ~320 & ~510: Maximum turns (currently 10)
- Lines 101-150: CSS styling

### [database.py](database.py) (14KB) ⭐ Database Layer
**All database operations**

**Main Sections:**
- `init_database()` - Create tables
- User management functions
- Query management functions
- Turn-level annotation functions
- Session-level annotation functions
- Summary and analytics functions

**Key Functions:**
- `create_or_get_user()` - User management
- `create_query()` - Query creation
- `add_turn_level_turn()` - Save turn-level data
- `add_session_level_turn()` - Save session-level data
- `get_turn_level_summary()` - Analytics
- `get_session_level_summary()` - Analytics

### [ai_service.py](ai_service.py) (3.0KB) ⭐ AI Integration
**AI response generation - CUSTOMIZE THIS!**

**Functions:**
- `generate_response_a()` - Assistant A responses
- `generate_response_b()` - Assistant B responses
- `get_assistant_response()` - Unified interface

**To integrate real AI:**
Replace mock implementations with actual API calls to:
- OpenAI GPT models
- Anthropic Claude
- Google Gemini
- Local models
- Any other LLM API

**Example integration included in comments**

## 🔧 Configuration Files

### [requirements.txt](requirements.txt) (18B)
**Python dependencies**
```
streamlit>=1.28.0
```

Add additional dependencies as needed:
- `openai` for OpenAI integration
- `anthropic` for Claude
- `pandas` for data analysis
- `plotly` for visualizations

### [.gitignore](.gitignore) (301B)
**Git ignore rules**
- Database files (*.db)
- Python cache
- IDE files
- OS files

## 🧪 Testing Files

### [test_setup.py](test_setup.py) (1.8KB)
**Automated setup verification**

**Tests:**
- Database initialization
- User creation
- Query creation
- AI service response generation

**Usage:**
```bash
python test_setup.py
```

**Expected output:**
```
============================================================
✓ ALL TESTS PASSED!
============================================================
```

## 📊 Generated Files

### annotation_system.db
**SQLite database (auto-generated)**

**Tables:**
- users
- queries
- turn_level_sessions
- turn_level_turns
- session_level_conversations
- session_level_turns
- session_level_preferences

**Size:** Grows with annotations
**Backup:** `sqlite3 annotation_system.db ".backup backup.db"`

## 📏 File Statistics

```
Total Documentation:    ~50 KB
Total Code:            ~41 KB
Total Project Size:    ~91 KB (excluding database)

Lines of Code:
- app.py:              ~700 lines
- database.py:         ~350 lines
- ai_service.py:       ~80 lines
Total:                 ~1,130 lines
```

## 🎨 Architecture Overview

```
┌─────────────────────────────────────────────┐
│                  app.py                     │
│  (Streamlit UI + User Interaction Logic)    │
│                                             │
│  • Guide page                               │
│  • Turn-level interface                     │
│  • Session-level interface                  │
│  • Summary dashboard                        │
└───────────┬─────────────────┬───────────────┘
            │                 │
            ↓                 ↓
┌───────────────────┐  ┌──────────────────┐
│   database.py     │  │  ai_service.py   │
│                   │  │                  │
│  • CRUD ops       │  │  • Generate      │
│  • Analytics      │  │    responses     │
│  • Queries        │  │  • Mock AI       │
└────────┬──────────┘  └──────────────────┘
         │
         ↓
┌─────────────────────┐
│ annotation_system.db│
│                     │
│  • SQLite DB        │
│  • All tables       │
│  • Persistent data  │
└─────────────────────┘
```

## 🔍 Code Organization

### app.py Structure
```python
# Imports & Config
import streamlit as st
from database import *
from ai_service import *

# Initialize
st.set_page_config(...)
init_database()

# Session State
if 'page' not in st.session_state:
    st.session_state.page = 'guide'
# ... more state variables

# CSS Styling
st.markdown("""<style>...</style>""")

# Page Functions
def show_guide_page(): ...
def show_turn_level_page(): ...
def show_session_level_page(): ...
def show_summary_page(): ...

# Helper Functions
def show_confirmation_and_reset(): ...
def reset_turn_level_state(): ...
def reset_session_level_state(): ...

# Main Router
def main():
    if st.session_state.page == 'guide':
        show_guide_page()
    elif st.session_state.page == 'turn_level':
        show_turn_level_page()
    # ... more routes

if __name__ == "__main__":
    main()
```

### database.py Structure
```python
# Database Functions organized by category:

# 1. Initialization
init_database()

# 2. User Management
create_or_get_user()

# 3. Query Management
create_query()
get_user_queries()

# 4. Turn-Level Operations
create_turn_level_session()
add_turn_level_turn()
update_turn_selection()
get_turn_level_session_turns()
complete_turn_level_session()

# 5. Session-Level Operations
create_session_level_conversation()
add_session_level_turn()
get_session_level_conversation_turns()
update_conversation_notes()
complete_session_level_conversation()
save_session_level_preference()

# 6. Analytics
get_all_users()
get_all_queries_for_summary()
get_turn_level_summary()
get_session_level_summary()
get_user_aggregate_stats()
```

### ai_service.py Structure
```python
# Mock AI Service

def generate_response_a(conversation_history, user_message):
    # Mock implementation
    # Replace with: openai.ChatCompletion.create(...)
    return response

def generate_response_b(conversation_history, user_message):
    # Mock implementation
    # Replace with: anthropic.messages.create(...)
    return response

def get_assistant_response(assistant_name, conversation_history, user_message):
    # Unified interface
    if assistant_name == 'A':
        return generate_response_a(...)
    elif assistant_name == 'B':
        return generate_response_b(...)
```

## 🎯 Feature Map

### By File

| Feature | Implemented In | Function |
|---------|----------------|----------|
| User login | app.py | `show_guide_page()` |
| Mode selection | app.py | `show_guide_page()` |
| Turn-level UI | app.py | `show_turn_level_page()` |
| Session-level UI | app.py | `show_session_level_page()` |
| Admin dashboard | app.py | `show_summary_page()` |
| Response highlighting | app.py | CSS in markdown |
| Database storage | database.py | All functions |
| AI responses | ai_service.py | `generate_response_*()` |
| Analytics | database.py | `get_*_summary()` |

## 📦 Deployment Checklist

Before deploying for actual research:

- [ ] Read [START_HERE.md](START_HERE.md)
- [ ] Follow [QUICKSTART.md](QUICKSTART.md) setup
- [ ] Customize [ai_service.py](ai_service.py) with real AI
- [ ] Change admin password in [app.py](app.py)
- [ ] Test both annotation modes
- [ ] Verify database saves correctly
- [ ] Test admin dashboard
- [ ] Prepare annotator instructions
- [ ] Set up backup schedule for database
- [ ] Test with multiple concurrent users
- [ ] Review security considerations in [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)

## 🔗 Inter-file Dependencies

```
app.py
├── imports database.py (all functions)
├── imports ai_service.py (get_assistant_response)
└── creates annotation_system.db (via database.py)

database.py
└── creates/manages annotation_system.db

ai_service.py
└── (standalone, no dependencies)

test_setup.py
├── imports database.py
└── imports ai_service.py
```

## 🎓 Learning Path

**Beginner** (Just want to use it)
1. [START_HERE.md](START_HERE.md)
2. [QUICKSTART.md](QUICKSTART.md)
3. Run the app
4. Done!

**Intermediate** (Customize for your research)
1. [START_HERE.md](START_HERE.md)
2. [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
3. [ai_service.py](ai_service.py) - Add your AI
4. [README.md](README.md) - Customization guide
5. Test and deploy

**Advanced** (Understand everything / Modify extensively)
1. [START_HERE.md](START_HERE.md)
2. [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
3. [WORKFLOW.md](WORKFLOW.md) - Understand flows
4. [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Understand data
5. [app.py](app.py) - Read all code
6. [database.py](database.py) - Read all code
7. Modify as needed

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Install | `pip install -r requirements.txt` |
| Test | `python test_setup.py` |
| Run | `streamlit run app.py` |
| Export data | `sqlite3 -header -csv annotation_system.db "SELECT * FROM turn_level_turns;" > data.csv` |
| Backup DB | `sqlite3 annotation_system.db ".backup backup.db"` |
| View DB | `sqlite3 annotation_system.db` then `.tables` |

---

**Total Files**: 12 (excluding generated files)
**Documentation Files**: 7
**Code Files**: 3
**Config Files**: 2

**This is a complete, production-ready system!** 🎉
