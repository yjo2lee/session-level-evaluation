# Database Schema Documentation

## Overview

The annotation system uses SQLite with 7 main tables to store user interactions, annotations, and preferences.

## Entity Relationship Diagram

```
┌─────────────┐
│   users     │
│─────────────│
│ user_id (PK)│
│ created_at  │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────┴──────────────────────────────────────────┐
│                                                  │
┌──────┴──────┐                          ┌────────┴────────┐
│   queries   │                          │  turn_level_    │
│─────────────│                          │   sessions      │
│ query_id(PK)│◄────────────────────────►│─────────────────│
│ user_id (FK)│                          │ session_id (PK) │
│ query_text  │                          │ user_id (FK)    │
│ created_at  │                          │ query_id (FK)   │
└──────┬──────┘                          │ started_at      │
       │                                 │ completed_at    │
       │ 1:N                             │ is_completed    │
       │                                 └────────┬────────┘
       │                                          │
       │                                          │ 1:N
       │                                          │
       │                                 ┌────────┴────────┐
       │                                 │  turn_level_    │
       │                                 │     turns       │
       │                                 │─────────────────│
       │                                 │ turn_id (PK)    │
       │                                 │ session_id (FK) │
       │                                 │ turn_number     │
       │                                 │ user_message    │
       │                                 │ response_a      │
       │                                 │ response_b      │
       │                                 │ selected_asst   │
       │                                 │ timestamp       │
       │                                 └─────────────────┘
       │
       │ 1:N
       │
┌──────┴────────────────┐
│ session_level_        │
│  conversations        │
│───────────────────────│
│ conversation_id (PK)  │
│ user_id (FK)          │
│ query_id (FK)         │
│ assistant_name        │
│ started_at            │
│ completed_at          │
│ is_completed          │
│ user_notes            │
└──────┬────────────────┘
       │
       │ 1:N
       │
┌──────┴────────────────┐
│ session_level_turns   │
│───────────────────────│
│ turn_id (PK)          │
│ conversation_id (FK)  │
│ turn_number           │
│ user_message          │
│ assistant_response    │
│ timestamp             │
└───────────────────────┘

┌───────────────────────────────┐
│ session_level_preferences     │
│───────────────────────────────│
│ preference_id (PK)            │
│ user_id (FK)                  │
│ query_id (FK)                 │
│ conversation_a_id (FK)        │
│ conversation_b_id (FK)        │
│ preferred_assistant           │
│ completed_at                  │
└───────────────────────────────┘
```

## Table Descriptions

### users
Stores basic user information.
- **user_id**: Unique identifier for each user (Primary Key)
- **created_at**: Timestamp when user was created

### queries
Stores the initial queries that users start their conversations with.
- **query_id**: Auto-incrementing unique identifier (Primary Key)
- **user_id**: Reference to the user who created the query (Foreign Key)
- **query_text**: The actual query text
- **created_at**: When the query was created

### turn_level_sessions
Represents a complete turn-level annotation session.
- **session_id**: Auto-incrementing unique identifier (Primary Key)
- **user_id**: Reference to the user (Foreign Key)
- **query_id**: Reference to the initial query (Foreign Key)
- **started_at**: When the session began
- **completed_at**: When the session was completed
- **is_completed**: Boolean flag indicating completion status

### turn_level_turns
Individual turns within a turn-level session.
- **turn_id**: Auto-incrementing unique identifier (Primary Key)
- **session_id**: Reference to the parent session (Foreign Key)
- **turn_number**: Sequential number of the turn (1, 2, 3, ...)
- **user_message**: What the user said
- **response_a**: Assistant A's response
- **response_b**: Assistant B's response
- **selected_assistant**: Which assistant was selected ('A' or 'B')
- **timestamp**: When the turn occurred

### session_level_conversations
A complete conversation with one assistant in session-level mode.
- **conversation_id**: Auto-incrementing unique identifier (Primary Key)
- **user_id**: Reference to the user (Foreign Key)
- **query_id**: Reference to the initial query (Foreign Key)
- **assistant_name**: Which assistant ('Assistant A' or 'Assistant B')
- **started_at**: When the conversation began
- **completed_at**: When the conversation was completed
- **is_completed**: Boolean flag indicating completion status
- **user_notes**: User's notes/reflections about this conversation

### session_level_turns
Individual turns within a session-level conversation.
- **turn_id**: Auto-incrementing unique identifier (Primary Key)
- **conversation_id**: Reference to the parent conversation (Foreign Key)
- **turn_number**: Sequential number of the turn (1, 2, 3, ...)
- **user_message**: What the user said
- **assistant_response**: What the assistant responded
- **timestamp**: When the turn occurred

### session_level_preferences
Stores the final preference after both session-level conversations.
- **preference_id**: Auto-incrementing unique identifier (Primary Key)
- **user_id**: Reference to the user (Foreign Key)
- **query_id**: Reference to the query (Foreign Key)
- **conversation_a_id**: Reference to conversation with Assistant A (Foreign Key)
- **conversation_b_id**: Reference to conversation with Assistant B (Foreign Key)
- **preferred_assistant**: Which assistant was preferred overall ('A' or 'B')
- **completed_at**: When the preference was recorded

## Data Flow

### Turn-Level Annotation Flow

1. User logs in → Create/retrieve entry in `users`
2. User enters first message → Create entry in `queries`
3. System creates annotation session → Create entry in `turn_level_sessions`
4. For each turn:
   - Generate both responses
   - Create entry in `turn_level_turns` with both responses
   - User selects preferred response
   - Update `selected_assistant` in `turn_level_turns`
5. Session ends → Update `is_completed` and `completed_at` in `turn_level_sessions`

### Session-Level Annotation Flow

1. User logs in → Create/retrieve entry in `users`
2. User enters first message → Create entry in `queries`
3. Start conversation with Assistant A → Create entry in `session_level_conversations`
4. For each turn:
   - Create entry in `session_level_turns`
5. User ends conversation → Update `is_completed` in `session_level_conversations`
6. User writes notes → Update `user_notes` in `session_level_conversations`
7. Repeat steps 3-6 for Assistant B
8. User selects preference → Create entry in `session_level_preferences`

## Query Examples

### Get all turns for a user's turn-level session
```sql
SELECT tlt.*
FROM turn_level_turns tlt
JOIN turn_level_sessions tls ON tlt.session_id = tls.session_id
WHERE tls.user_id = 'user123' AND tls.query_id = 1;
```

### Calculate selection ratio for a query
```sql
SELECT
    selected_assistant,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM turn_level_turns tlt
JOIN turn_level_sessions tls ON tlt.session_id = tls.session_id
WHERE tls.user_id = 'user123' AND tls.query_id = 1
GROUP BY selected_assistant;
```

### Get session-level conversations with notes
```sql
SELECT
    slc.assistant_name,
    slc.user_notes,
    slp.preferred_assistant
FROM session_level_conversations slc
JOIN session_level_preferences slp ON slc.query_id = slp.query_id
WHERE slc.user_id = 'user123' AND slc.query_id = 1;
```

### Check consistency between turn and session preferences
```sql
WITH turn_pref AS (
    SELECT
        tls.user_id,
        tls.query_id,
        CASE
            WHEN SUM(CASE WHEN tlt.selected_assistant = 'A' THEN 1 ELSE 0 END) >
                 SUM(CASE WHEN tlt.selected_assistant = 'B' THEN 1 ELSE 0 END)
            THEN 'A' ELSE 'B'
        END as preferred_assistant
    FROM turn_level_turns tlt
    JOIN turn_level_sessions tls ON tlt.session_id = tls.session_id
    WHERE tls.is_completed = 1
    GROUP BY tls.user_id, tls.query_id
)
SELECT
    tp.user_id,
    tp.query_id,
    tp.preferred_assistant as turn_level_preference,
    slp.preferred_assistant as session_level_preference,
    CASE
        WHEN tp.preferred_assistant = slp.preferred_assistant
        THEN 'Consistent'
        ELSE 'Inconsistent'
    END as consistency
FROM turn_pref tp
JOIN session_level_preferences slp
    ON tp.user_id = slp.user_id AND tp.query_id = slp.query_id;
```

## Backup and Export

### Backup the entire database
```bash
sqlite3 annotation_system.db ".backup annotation_system_backup.db"
```

### Export to CSV
```bash
sqlite3 -header -csv annotation_system.db "SELECT * FROM turn_level_turns;" > turn_level_turns.csv
```

### Export to JSON (using Python)
```python
import sqlite3
import json

conn = sqlite3.connect('annotation_system.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM turn_level_turns")
rows = cursor.fetchall()
columns = [description[0] for description in cursor.description]
data = [dict(zip(columns, row)) for row in rows]

with open('turn_level_turns.json', 'w') as f:
    json.dump(data, f, indent=2)
```
