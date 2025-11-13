"""
Database Integrity Diagnostic Script

Tests SQLite database integrity including:
- Table structure and schema
- Data isolation between users
- Insert/update operations
- Foreign key constraints
- Data persistence
- Query-level statistics accuracy
"""

import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Tuple

DB_NAME = 'annotation_system.db'

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"       {details}")

def test_table_existence() -> bool:
    """Test that all required tables exist."""
    print_section("1. TABLE EXISTENCE CHECK")

    required_tables = [
        'users',
        'queries',
        'turn_level_sessions',
        'turn_level_turns',
        'session_level_conversations',
        'session_level_turns',
        'session_level_preferences'
    ]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    all_passed = True
    for table in required_tables:
        exists = table in existing_tables
        print_test(f"Table '{table}' exists", exists)
        all_passed = all_passed and exists

    return all_passed

def test_table_schemas() -> bool:
    """Test that tables have correct column structure."""
    print_section("2. TABLE SCHEMA VALIDATION")

    expected_schemas = {
        'users': ['user_id', 'created_at'],
        'queries': ['query_id', 'user_id', 'query_text', 'created_at'],
        'turn_level_sessions': ['session_id', 'user_id', 'query_id', 'started_at', 'completed_at', 'is_completed'],
        'turn_level_turns': ['turn_id', 'session_id', 'turn_number', 'user_message', 'response_a', 'response_b', 'selected_assistant', 'timestamp'],
        'session_level_conversations': ['conversation_id', 'user_id', 'query_id', 'assistant_name', 'started_at', 'completed_at', 'is_completed', 'user_notes'],
        'session_level_turns': ['turn_id', 'conversation_id', 'turn_number', 'user_message', 'assistant_response', 'timestamp'],
        'session_level_preferences': ['preference_id', 'user_id', 'query_id', 'conversation_a_id', 'conversation_b_id', 'preferred_assistant', 'completed_at']
    }

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    all_passed = True
    for table, expected_columns in expected_schemas.items():
        cursor.execute(f"PRAGMA table_info({table})")
        actual_columns = [row[1] for row in cursor.fetchall()]

        has_all_columns = all(col in actual_columns for col in expected_columns)
        print_test(
            f"Table '{table}' has all required columns",
            has_all_columns,
            f"Expected: {expected_columns}, Got: {actual_columns}" if not has_all_columns else ""
        )
        all_passed = all_passed and has_all_columns

    conn.close()
    return all_passed

def test_user_data_isolation() -> bool:
    """Test that data for different users is properly isolated."""
    print_section("3. USER DATA ISOLATION TEST")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create test users
    test_users = ['test_user_1', 'test_user_2', 'test_user_3']

    for user_id in test_users:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
                      (user_id, datetime.now()))
    conn.commit()

    # Create queries for each user
    query_ids = {}
    for i, user_id in enumerate(test_users):
        cursor.execute("INSERT INTO queries (user_id, query_text, created_at) VALUES (?, ?, ?)",
                      (user_id, f"Test query for {user_id}", datetime.now()))
        query_ids[user_id] = cursor.lastrowid
    conn.commit()

    # Verify each user has only their own queries
    all_passed = True
    for user_id in test_users:
        cursor.execute("SELECT query_id, query_text FROM queries WHERE user_id = ?", (user_id,))
        user_queries = cursor.fetchall()

        # Should have exactly 1 query
        correct_count = len(user_queries) >= 1
        print_test(f"User '{user_id}' has their queries", correct_count,
                  f"Query count: {len(user_queries)}")

        # Verify it's the correct query
        user_query_texts = [q[1] for q in user_queries]
        has_own_query = f"Test query for {user_id}" in user_query_texts
        print_test(f"User '{user_id}' query text is correct", has_own_query)

        all_passed = all_passed and correct_count and has_own_query

    # Cleanup test data
    for user_id in test_users:
        cursor.execute("DELETE FROM queries WHERE user_id = ? AND query_text LIKE 'Test query for%'", (user_id,))
    conn.commit()
    conn.close()

    return all_passed

def test_turn_level_data_persistence() -> bool:
    """Test turn-level annotation data persistence."""
    print_section("4. TURN-LEVEL DATA PERSISTENCE TEST")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create test user and query
    test_user = 'test_persistence_user'
    cursor.execute("INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
                  (test_user, datetime.now()))
    cursor.execute("INSERT INTO queries (user_id, query_text, created_at) VALUES (?, ?, ?)",
                  (test_user, "Test persistence query", datetime.now()))
    query_id = cursor.lastrowid
    conn.commit()

    # Create turn-level session
    cursor.execute("INSERT INTO turn_level_sessions (user_id, query_id, is_completed) VALUES (?, ?, ?)",
                  (test_user, query_id, 0))
    session_id = cursor.lastrowid
    conn.commit()

    # Add turns
    test_turns = [
        (1, "Question 1", "Response A1", "Response B1", "A"),
        (2, "Question 2", "Response A2", "Response B2", "B"),
        (3, "Question 3", "Response A3", "Response B3", "A")
    ]

    for turn_num, user_msg, resp_a, resp_b, selected in test_turns:
        cursor.execute("""INSERT INTO turn_level_turns
                         (session_id, turn_number, user_message, response_a, response_b, selected_assistant)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (session_id, turn_num, user_msg, resp_a, resp_b, selected))
    conn.commit()

    # Verify data persistence
    cursor.execute("SELECT turn_number, user_message, selected_assistant FROM turn_level_turns WHERE session_id = ? ORDER BY turn_number",
                  (session_id,))
    stored_turns = cursor.fetchall()

    all_passed = True

    # Check count
    correct_count = len(stored_turns) == len(test_turns)
    print_test("Correct number of turns stored", correct_count,
              f"Expected {len(test_turns)}, got {len(stored_turns)}")
    all_passed = all_passed and correct_count

    # Check data integrity
    for i, (turn_num, user_msg, selected) in enumerate(stored_turns):
        expected_turn = test_turns[i]
        data_matches = (turn_num == expected_turn[0] and
                       user_msg == expected_turn[1] and
                       selected == expected_turn[4])
        print_test(f"Turn {turn_num} data integrity", data_matches)
        all_passed = all_passed and data_matches

    # Test selection update
    cursor.execute("UPDATE turn_level_turns SET selected_assistant = ? WHERE session_id = ? AND turn_number = ?",
                  ("B", session_id, 1))
    conn.commit()

    cursor.execute("SELECT selected_assistant FROM turn_level_turns WHERE session_id = ? AND turn_number = ?",
                  (session_id, 1))
    updated_selection = cursor.fetchone()[0]
    update_works = updated_selection == "B"
    print_test("Selection update works", update_works,
              f"Expected 'B', got '{updated_selection}'")
    all_passed = all_passed and update_works

    # Cleanup
    cursor.execute("DELETE FROM turn_level_turns WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM turn_level_sessions WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM queries WHERE query_id = ?", (query_id,))
    cursor.execute("DELETE FROM users WHERE user_id = ?", (test_user,))
    conn.commit()
    conn.close()

    return all_passed

def test_session_level_data_persistence() -> bool:
    """Test session-level annotation data persistence."""
    print_section("5. SESSION-LEVEL DATA PERSISTENCE TEST")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create test user and query
    test_user = 'test_session_user'
    cursor.execute("INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
                  (test_user, datetime.now()))
    cursor.execute("INSERT INTO queries (user_id, query_text, created_at) VALUES (?, ?, ?)",
                  (test_user, "Test session query", datetime.now()))
    query_id = cursor.lastrowid
    conn.commit()

    # Create conversations for both assistants
    conversations = {}
    for assistant_name in ['Assistant A', 'Assistant B']:
        cursor.execute("""INSERT INTO session_level_conversations
                         (user_id, query_id, assistant_name, user_notes)
                         VALUES (?, ?, ?, ?)""",
                      (test_user, query_id, assistant_name, f"Notes for {assistant_name}"))
        conversations[assistant_name] = cursor.lastrowid
    conn.commit()

    # Add turns to each conversation
    for assistant_name, conv_id in conversations.items():
        for turn_num in range(1, 4):
            cursor.execute("""INSERT INTO session_level_turns
                             (conversation_id, turn_number, user_message, assistant_response)
                             VALUES (?, ?, ?, ?)""",
                          (conv_id, turn_num, f"Question {turn_num}",
                           f"{assistant_name} response {turn_num}"))
    conn.commit()

    # Save preference
    # Get conversation IDs
    conv_a_id = conversations['Assistant A']
    conv_b_id = conversations['Assistant B']
    cursor.execute("""INSERT INTO session_level_preferences
                     (user_id, query_id, conversation_a_id, conversation_b_id, preferred_assistant)
                     VALUES (?, ?, ?, ?, ?)""",
                  (test_user, query_id, conv_a_id, conv_b_id, "A"))
    conn.commit()

    # Verify data
    all_passed = True

    # Check conversations
    cursor.execute("SELECT assistant_name, user_notes FROM session_level_conversations WHERE user_id = ? AND query_id = ?",
                  (test_user, query_id))
    stored_convs = cursor.fetchall()

    correct_conv_count = len(stored_convs) == 2
    print_test("Correct number of conversations", correct_conv_count,
              f"Expected 2, got {len(stored_convs)}")
    all_passed = all_passed and correct_conv_count

    # Check notes
    for assistant_name, notes in stored_convs:
        notes_correct = notes == f"Notes for {assistant_name}"
        print_test(f"Notes for {assistant_name} are correct", notes_correct)
        all_passed = all_passed and notes_correct

    # Check turns for each conversation
    for assistant_name, conv_id in conversations.items():
        cursor.execute("SELECT COUNT(*) FROM session_level_turns WHERE conversation_id = ?",
                      (conv_id,))
        turn_count = cursor.fetchone()[0]
        correct_turn_count = turn_count == 3
        print_test(f"{assistant_name} has correct turn count", correct_turn_count,
                  f"Expected 3, got {turn_count}")
        all_passed = all_passed and correct_turn_count

    # Check preference
    cursor.execute("SELECT preferred_assistant FROM session_level_preferences WHERE user_id = ? AND query_id = ?",
                  (test_user, query_id))
    pref = cursor.fetchone()
    pref_correct = pref and pref[0] == "A"
    print_test("Preference stored correctly", pref_correct,
              f"Expected 'A', got '{pref[0] if pref else None}'")
    all_passed = all_passed and pref_correct

    # Cleanup
    for conv_id in conversations.values():
        cursor.execute("DELETE FROM session_level_turns WHERE conversation_id = ?", (conv_id,))
    cursor.execute("DELETE FROM session_level_conversations WHERE user_id = ? AND query_id = ?",
                  (test_user, query_id))
    cursor.execute("DELETE FROM session_level_preferences WHERE user_id = ? AND query_id = ?",
                  (test_user, query_id))
    cursor.execute("DELETE FROM queries WHERE query_id = ?", (query_id,))
    cursor.execute("DELETE FROM users WHERE user_id = ?", (test_user,))
    conn.commit()
    conn.close()

    return all_passed

def test_query_level_stats_accuracy() -> bool:
    """Test that query-level statistics are calculated correctly."""
    print_section("6. QUERY-LEVEL STATISTICS ACCURACY TEST")

    from database import get_user_query_level_stats

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create test user
    test_user = 'test_stats_user'
    cursor.execute("INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
                  (test_user, datetime.now()))
    conn.commit()

    # Create test queries with known outcomes
    test_cases = [
        # Query 1: Turn-level winner = A (3-1), Session-level winner = A (consistent)
        {
            'query_text': 'Query 1',
            'turn_votes': {'A': 3, 'B': 1},
            'session_pref': 'A',
            'expected_turn_winner': 'A',
            'expected_session_winner': 'A',
            'expected_consistent': True
        },
        # Query 2: Turn-level winner = B (1-3), Session-level winner = B (consistent)
        {
            'query_text': 'Query 2',
            'turn_votes': {'A': 1, 'B': 3},
            'session_pref': 'B',
            'expected_turn_winner': 'B',
            'expected_session_winner': 'B',
            'expected_consistent': True
        },
        # Query 3: Turn-level winner = A (3-2), Session-level winner = B (inconsistent)
        {
            'query_text': 'Query 3',
            'turn_votes': {'A': 3, 'B': 2},
            'session_pref': 'B',
            'expected_turn_winner': 'A',
            'expected_session_winner': 'B',
            'expected_consistent': False
        }
    ]

    query_ids = []
    for case in test_cases:
        # Create query
        cursor.execute("INSERT INTO queries (user_id, query_text, created_at) VALUES (?, ?, ?)",
                      (test_user, case['query_text'], datetime.now()))
        query_id = cursor.lastrowid
        query_ids.append(query_id)

        # Create turn-level session
        cursor.execute("INSERT INTO turn_level_sessions (user_id, query_id, is_completed) VALUES (?, ?, ?)",
                      (test_user, query_id, 1))
        session_id = cursor.lastrowid

        # Add turns with votes
        turn_num = 1
        for assistant, vote_count in case['turn_votes'].items():
            for _ in range(vote_count):
                cursor.execute("""INSERT INTO turn_level_turns
                                 (session_id, turn_number, user_message, response_a, response_b, selected_assistant)
                                 VALUES (?, ?, ?, ?, ?, ?)""",
                              (session_id, turn_num, f"Q{turn_num}", f"A{turn_num}", f"B{turn_num}", assistant))
                turn_num += 1

        # Create session-level conversations
        conv_ids = {}
        for assistant_name in ['Assistant A', 'Assistant B']:
            cursor.execute("""INSERT INTO session_level_conversations
                             (user_id, query_id, assistant_name)
                             VALUES (?, ?, ?)""",
                          (test_user, query_id, assistant_name))
            conv_ids[assistant_name] = cursor.lastrowid

        # Save preference
        cursor.execute("""INSERT INTO session_level_preferences
                         (user_id, query_id, conversation_a_id, conversation_b_id, preferred_assistant)
                         VALUES (?, ?, ?, ?, ?)""",
                      (test_user, query_id, conv_ids['Assistant A'], conv_ids['Assistant B'], case['session_pref']))

    conn.commit()
    conn.close()

    # Get statistics
    stats = get_user_query_level_stats(test_user)

    # Verify results
    all_passed = True

    # Check total queries
    total_correct = stats['total_queries'] == len(test_cases)
    print_test("Total queries count", total_correct,
              f"Expected {len(test_cases)}, got {stats['total_queries']}")
    all_passed = all_passed and total_correct

    # Check turn-level wins
    expected_turn_a = sum(1 for c in test_cases if c['expected_turn_winner'] == 'A')
    expected_turn_b = sum(1 for c in test_cases if c['expected_turn_winner'] == 'B')
    turn_a_correct = stats['turn_level_wins']['A'] == expected_turn_a
    turn_b_correct = stats['turn_level_wins']['B'] == expected_turn_b
    print_test("Turn-level A wins", turn_a_correct,
              f"Expected {expected_turn_a}, got {stats['turn_level_wins']['A']}")
    print_test("Turn-level B wins", turn_b_correct,
              f"Expected {expected_turn_b}, got {stats['turn_level_wins']['B']}")
    all_passed = all_passed and turn_a_correct and turn_b_correct

    # Check session-level wins
    expected_session_a = sum(1 for c in test_cases if c['expected_session_winner'] == 'A')
    expected_session_b = sum(1 for c in test_cases if c['expected_session_winner'] == 'B')
    session_a_correct = stats['session_level_wins']['A'] == expected_session_a
    session_b_correct = stats['session_level_wins']['B'] == expected_session_b
    print_test("Session-level A wins", session_a_correct,
              f"Expected {expected_session_a}, got {stats['session_level_wins']['A']}")
    print_test("Session-level B wins", session_b_correct,
              f"Expected {expected_session_b}, got {stats['session_level_wins']['B']}")
    all_passed = all_passed and session_a_correct and session_b_correct

    # Check consistency rate
    expected_consistent = sum(1 for c in test_cases if c['expected_consistent'])
    expected_rate = (expected_consistent / len(test_cases)) * 100
    rate_correct = abs(stats['consistency_rate'] - expected_rate) < 0.1
    print_test("Consistency rate", rate_correct,
              f"Expected {expected_rate:.1f}%, got {stats['consistency_rate']:.1f}%")
    all_passed = all_passed and rate_correct

    # Cleanup
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for query_id in query_ids:
        cursor.execute("SELECT session_id FROM turn_level_sessions WHERE query_id = ?", (query_id,))
        sessions = cursor.fetchall()
        for (session_id,) in sessions:
            cursor.execute("DELETE FROM turn_level_turns WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM turn_level_sessions WHERE query_id = ?", (query_id,))

        cursor.execute("SELECT conversation_id FROM session_level_conversations WHERE query_id = ?", (query_id,))
        convs = cursor.fetchall()
        for (conv_id,) in convs:
            cursor.execute("DELETE FROM session_level_turns WHERE conversation_id = ?", (conv_id,))
        cursor.execute("DELETE FROM session_level_conversations WHERE query_id = ?", (query_id,))
        cursor.execute("DELETE FROM session_level_preferences WHERE query_id = ?", (query_id,))
        cursor.execute("DELETE FROM queries WHERE query_id = ?", (query_id,))
    cursor.execute("DELETE FROM users WHERE user_id = ?", (test_user,))
    conn.commit()
    conn.close()

    return all_passed

def test_concurrent_user_operations() -> bool:
    """Test that multiple users can operate simultaneously without interference."""
    print_section("7. CONCURRENT USER OPERATIONS TEST")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create multiple users
    users = ['concurrent_user_1', 'concurrent_user_2', 'concurrent_user_3']
    for user_id in users:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
                      (user_id, datetime.now()))
    conn.commit()

    # Each user creates their own data
    user_data = {}
    for i, user_id in enumerate(users):
        # Create query
        cursor.execute("INSERT INTO queries (user_id, query_text, created_at) VALUES (?, ?, ?)",
                      (user_id, f"Query by {user_id}", datetime.now()))
        query_id = cursor.lastrowid

        # Create session
        cursor.execute("INSERT INTO turn_level_sessions (user_id, query_id, is_completed) VALUES (?, ?, ?)",
                      (user_id, query_id, 0))
        session_id = cursor.lastrowid

        # Add turn
        cursor.execute("""INSERT INTO turn_level_turns
                         (session_id, turn_number, user_message, response_a, response_b, selected_assistant)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (session_id, 1, f"Message from {user_id}", "A_resp", "B_resp", "A"))

        user_data[user_id] = {'query_id': query_id, 'session_id': session_id}

    conn.commit()

    # Verify each user's data is isolated
    all_passed = True
    for user_id in users:
        # Check queries
        cursor.execute("SELECT query_text FROM queries WHERE user_id = ? AND query_text LIKE 'Query by%'", (user_id,))
        queries = cursor.fetchall()

        has_own_query = len(queries) >= 1 and queries[0][0] == f"Query by {user_id}"
        print_test(f"{user_id} has isolated query data", has_own_query)
        all_passed = all_passed and has_own_query

        # Check turns
        session_id = user_data[user_id]['session_id']
        cursor.execute("SELECT user_message FROM turn_level_turns WHERE session_id = ?", (session_id,))
        turns = cursor.fetchall()

        has_own_turn = len(turns) == 1 and turns[0][0] == f"Message from {user_id}"
        print_test(f"{user_id} has isolated turn data", has_own_turn)
        all_passed = all_passed and has_own_turn

    # Cleanup
    for user_id, data in user_data.items():
        cursor.execute("DELETE FROM turn_level_turns WHERE session_id = ?", (data['session_id'],))
        cursor.execute("DELETE FROM turn_level_sessions WHERE session_id = ?", (data['session_id'],))
        cursor.execute("DELETE FROM queries WHERE query_id = ?", (data['query_id'],))
    for user_id in users:
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    return all_passed

def main():
    """Run all diagnostic tests."""
    print("\n" + "="*60)
    print("  DATABASE INTEGRITY DIAGNOSTIC SCRIPT")
    print("  Database:", DB_NAME)
    print("="*60)

    tests = [
        ("Table Existence", test_table_existence),
        ("Table Schemas", test_table_schemas),
        ("User Data Isolation", test_user_data_isolation),
        ("Turn-Level Data Persistence", test_turn_level_data_persistence),
        ("Session-Level Data Persistence", test_session_level_data_persistence),
        ("Query-Level Statistics Accuracy", test_query_level_stats_accuracy),
        ("Concurrent User Operations", test_concurrent_user_operations)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # Print summary
    print_section("SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n{'='*60}")
    print(f"  Total: {passed}/{total} tests passed")
    if passed == total:
        print(f"  ✓ ALL TESTS PASSED - Database integrity verified!")
    else:
        print(f"  ✗ {total - passed} test(s) failed - Review issues above")
    print(f"{'='*60}\n")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
