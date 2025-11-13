import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DB_NAME = "annotation_system.db"

def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table for users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for queries (stores the initial query used across sessions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            query_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            query_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Table for turn-level annotations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turn_level_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            query_id INTEGER,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            is_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (query_id) REFERENCES queries(query_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turn_level_turns (
            turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            turn_number INTEGER,
            user_message TEXT,
            response_a TEXT,
            response_b TEXT,
            selected_assistant TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES turn_level_sessions(session_id)
        )
    """)

    # Table for session-level annotations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_level_conversations (
            conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            query_id INTEGER,
            assistant_name TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            is_completed BOOLEAN DEFAULT 0,
            user_notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (query_id) REFERENCES queries(query_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_level_turns (
            turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            turn_number INTEGER,
            user_message TEXT,
            assistant_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES session_level_conversations(conversation_id)
        )
    """)

    # Table for session-level overall preference
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_level_preferences (
            preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            query_id INTEGER,
            conversation_a_id INTEGER,
            conversation_b_id INTEGER,
            preferred_assistant TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (query_id) REFERENCES queries(query_id),
            FOREIGN KEY (conversation_a_id) REFERENCES session_level_conversations(conversation_id),
            FOREIGN KEY (conversation_b_id) REFERENCES session_level_conversations(conversation_id)
        )
    """)

    conn.commit()
    conn.close()

# ============= User Management =============

def create_or_get_user(user_id: str) -> str:
    """Create a new user or get existing user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    return user_id

# ============= Query Management =============

def create_query(user_id: str, query_text: str) -> int:
    """Create a new query and return its ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO queries (user_id, query_text) VALUES (?, ?)",
        (user_id, query_text)
    )
    query_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return query_id

def get_user_queries(user_id: str) -> List[Tuple[int, str]]:
    """Get all queries for a user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT query_id, query_text FROM queries WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    queries = cursor.fetchall()
    conn.close()
    return queries

# ============= Turn-Level Annotation =============

def create_turn_level_session(user_id: str, query_id: int) -> int:
    """Create a new turn-level annotation session."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO turn_level_sessions (user_id, query_id) VALUES (?, ?)",
        (user_id, query_id)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def add_turn_level_turn(
    session_id: int,
    turn_number: int,
    user_message: str,
    response_a: str,
    response_b: str,
    selected_assistant: Optional[str] = None
) -> int:
    """Add a turn to a turn-level session."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO turn_level_turns
           (session_id, turn_number, user_message, response_a, response_b, selected_assistant)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (session_id, turn_number, user_message, response_a, response_b, selected_assistant)
    )
    turn_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return turn_id

def update_turn_selection(turn_id: int, selected_assistant: str):
    """Update the selected assistant for a turn."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE turn_level_turns SET selected_assistant = ? WHERE turn_id = ?",
        (selected_assistant, turn_id)
    )
    conn.commit()
    conn.close()

def get_turn_level_session_turns(session_id: int) -> List[Dict]:
    """Get all turns for a turn-level session."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT turn_id, turn_number, user_message, response_a, response_b, selected_assistant
           FROM turn_level_turns WHERE session_id = ? ORDER BY turn_number""",
        (session_id,)
    )
    turns = []
    for row in cursor.fetchall():
        turns.append({
            'turn_id': row[0],
            'turn_number': row[1],
            'user_message': row[2],
            'response_a': row[3],
            'response_b': row[4],
            'selected_assistant': row[5]
        })
    conn.close()
    return turns

def complete_turn_level_session(session_id: int):
    """Mark a turn-level session as completed."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE turn_level_sessions SET is_completed = 1, completed_at = ? WHERE session_id = ?",
        (datetime.now(), session_id)
    )
    conn.commit()
    conn.close()

# ============= Session-Level Annotation =============

def create_session_level_conversation(user_id: str, query_id: int, assistant_name: str) -> int:
    """Create a new session-level conversation."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO session_level_conversations (user_id, query_id, assistant_name) VALUES (?, ?, ?)",
        (user_id, query_id, assistant_name)
    )
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return conversation_id

def add_session_level_turn(
    conversation_id: int,
    turn_number: int,
    user_message: str,
    assistant_response: str
) -> int:
    """Add a turn to a session-level conversation."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO session_level_turns
           (conversation_id, turn_number, user_message, assistant_response)
           VALUES (?, ?, ?, ?)""",
        (conversation_id, turn_number, user_message, assistant_response)
    )
    turn_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return turn_id

def get_session_level_conversation_turns(conversation_id: int) -> List[Dict]:
    """Get all turns for a session-level conversation."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT turn_number, user_message, assistant_response
           FROM session_level_turns WHERE conversation_id = ? ORDER BY turn_number""",
        (conversation_id,)
    )
    turns = []
    for row in cursor.fetchall():
        turns.append({
            'turn_number': row[0],
            'user_message': row[1],
            'assistant_response': row[2]
        })
    conn.close()
    return turns

def update_conversation_notes(conversation_id: int, notes: str):
    """Update the notes for a conversation."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE session_level_conversations SET user_notes = ? WHERE conversation_id = ?",
        (notes, conversation_id)
    )
    conn.commit()
    conn.close()

def complete_session_level_conversation(conversation_id: int):
    """Mark a session-level conversation as completed."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE session_level_conversations SET is_completed = 1, completed_at = ? WHERE conversation_id = ?",
        (datetime.now(), conversation_id)
    )
    conn.commit()
    conn.close()

def save_session_level_preference(
    user_id: str,
    query_id: int,
    conversation_a_id: int,
    conversation_b_id: int,
    preferred_assistant: str
):
    """Save the overall preference for session-level annotation."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO session_level_preferences
           (user_id, query_id, conversation_a_id, conversation_b_id, preferred_assistant)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, query_id, conversation_a_id, conversation_b_id, preferred_assistant)
    )
    conn.commit()
    conn.close()

# ============= Summary and Analytics =============

def get_all_users() -> List[str]:
    """Get all user IDs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM users ORDER BY user_id")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_all_queries_for_summary() -> List[Tuple[int, str, str]]:
    """Get all queries with their IDs and user IDs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT query_id, user_id, query_text FROM queries ORDER BY created_at DESC")
    queries = cursor.fetchall()
    conn.close()
    return queries

def get_turn_level_summary(user_id: str, query_id: int) -> Dict:
    """Get turn-level annotation summary for a user and query."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get all sessions for this user and query
    cursor.execute(
        """SELECT session_id FROM turn_level_sessions
           WHERE user_id = ? AND query_id = ? AND is_completed = 1""",
        (user_id, query_id)
    )
    sessions = cursor.fetchall()

    all_turns = []
    total_a = 0
    total_b = 0

    for (session_id,) in sessions:
        turns = get_turn_level_session_turns(session_id)
        all_turns.extend(turns)
        for turn in turns:
            if turn['selected_assistant'] == 'A':
                total_a += 1
            elif turn['selected_assistant'] == 'B':
                total_b += 1

    conn.close()

    total = total_a + total_b
    return {
        'turns': all_turns,
        'model_a_count': total_a,
        'model_b_count': total_b,
        'model_a_ratio': total_a / total if total > 0 else 0,
        'model_b_ratio': total_b / total if total > 0 else 0
    }

def get_session_level_summary(user_id: str, query_id: int) -> Dict:
    """Get session-level annotation summary for a user and query."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get all conversations
    cursor.execute(
        """SELECT conversation_id, assistant_name, user_notes
           FROM session_level_conversations
           WHERE user_id = ? AND query_id = ? AND is_completed = 1
           ORDER BY started_at""",
        (user_id, query_id)
    )
    conversations = cursor.fetchall()

    conversation_data = []
    for conv_id, assistant_name, notes in conversations:
        turns = get_session_level_conversation_turns(conv_id)
        conversation_data.append({
            'conversation_id': conv_id,
            'assistant_name': assistant_name,
            'turns': turns,
            'notes': notes
        })

    # Get overall preference
    cursor.execute(
        """SELECT preferred_assistant FROM session_level_preferences
           WHERE user_id = ? AND query_id = ?""",
        (user_id, query_id)
    )
    result = cursor.fetchone()
    preferred = result[0] if result else None

    conn.close()

    return {
        'conversations': conversation_data,
        'preferred_assistant': preferred
    }

def get_user_aggregate_stats(user_id: str) -> Dict:
    """Get aggregate statistics for a user across all queries."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Turn-level stats
    cursor.execute(
        """SELECT selected_assistant, COUNT(*)
           FROM turn_level_turns tlt
           JOIN turn_level_sessions tls ON tlt.session_id = tls.session_id
           WHERE tls.user_id = ? AND tls.is_completed = 1 AND selected_assistant IS NOT NULL
           GROUP BY selected_assistant""",
        (user_id,)
    )
    turn_stats = dict(cursor.fetchall())

    # Session-level stats
    cursor.execute(
        """SELECT preferred_assistant, COUNT(*)
           FROM session_level_preferences
           WHERE user_id = ?
           GROUP BY preferred_assistant""",
        (user_id,)
    )
    session_stats = dict(cursor.fetchall())

    conn.close()

    return {
        'turn_level': turn_stats,
        'session_level': session_stats
    }

def get_user_query_level_stats(user_id: str) -> Dict:
    """Get per-query statistics for a user showing winners at each level.

    Returns:
        Dict containing:
        - turn_level_wins: {'A': count, 'B': count} - queries won by each model at turn level
        - session_level_wins: {'A': count, 'B': count} - queries won by each model at session level
        - consistency_rate: float (0-100) - percentage of queries where both levels agreed
        - query_details: List of dicts with per-query breakdown
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get all queries for this user that have been annotated
    cursor.execute(
        """SELECT DISTINCT q.query_id, q.query_text
           FROM queries q
           WHERE q.user_id = ?
           ORDER BY q.query_id""",
        (user_id,)
    )
    queries = cursor.fetchall()

    turn_level_wins = {'A': 0, 'B': 0}
    session_level_wins = {'A': 0, 'B': 0}
    consistent_count = 0
    total_queries = 0
    query_details = []

    for query_id, query_text in queries:
        # Get turn-level winner (majority vote across all turns for this query)
        cursor.execute(
            """SELECT selected_assistant, COUNT(*) as count
               FROM turn_level_turns tlt
               JOIN turn_level_sessions tls ON tlt.session_id = tls.session_id
               WHERE tls.user_id = ? AND tls.query_id = ? AND tlt.selected_assistant IS NOT NULL
               GROUP BY selected_assistant""",
            (user_id, query_id)
        )
        turn_votes = dict(cursor.fetchall())

        # Get session-level winner
        cursor.execute(
            """SELECT preferred_assistant
               FROM session_level_preferences
               WHERE user_id = ? AND query_id = ?""",
            (user_id, query_id)
        )
        session_pref_row = cursor.fetchone()

        # Get notes for both assistants
        cursor.execute(
            """SELECT assistant_name, user_notes
               FROM session_level_conversations
               WHERE user_id = ? AND query_id = ?""",
            (user_id, query_id)
        )
        notes_rows = cursor.fetchall()
        notes_dict = {row[0]: row[1] for row in notes_rows}

        # Determine winners
        turn_winner = None
        session_winner = None

        if turn_votes:
            a_votes = turn_votes.get('A', 0)
            b_votes = turn_votes.get('B', 0)
            if a_votes > b_votes:
                turn_winner = 'A'
                turn_level_wins['A'] += 1
            elif b_votes > a_votes:
                turn_winner = 'B'
                turn_level_wins['B'] += 1
            # If tie, no winner counted

            if session_pref_row:
                session_winner = session_pref_row[0]
                session_level_wins[session_winner] += 1

            # Check consistency
            if turn_winner and session_winner:
                total_queries += 1
                is_consistent = (turn_winner == session_winner)
                if is_consistent:
                    consistent_count += 1

                query_details.append({
                    'query_id': query_id,
                    'query_text': query_text,
                    'turn_winner': turn_winner,
                    'turn_votes': {'A': a_votes, 'B': b_votes},
                    'session_winner': session_winner,
                    'consistent': is_consistent,
                    'notes_a': notes_dict.get('Assistant A', ''),
                    'notes_b': notes_dict.get('Assistant B', '')
                })

    conn.close()

    consistency_rate = (consistent_count / total_queries * 100) if total_queries > 0 else 0

    return {
        'turn_level_wins': turn_level_wins,
        'session_level_wins': session_level_wins,
        'consistency_rate': consistency_rate,
        'total_queries': total_queries,
        'query_details': query_details
    }
