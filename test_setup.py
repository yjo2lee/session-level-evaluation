"""
Quick test script to verify database and basic functionality.
Run this before starting the Streamlit app to ensure everything is set up correctly.
"""

from database import init_database, create_or_get_user, create_query
from ai_service import get_assistant_response

def test_database():
    """Test database initialization and basic operations."""
    print("Testing database initialization...")
    init_database()
    print("✓ Database initialized successfully")

    print("\nTesting user creation...")
    user_id = create_or_get_user("test_user")
    print(f"✓ User created: {user_id}")

    print("\nTesting query creation...")
    query_id = create_query(user_id, "What is Python?")
    print(f"✓ Query created with ID: {query_id}")

    print("\nAll database tests passed!")

def test_ai_service():
    """Test AI service mock responses."""
    print("\nTesting AI response generation...")

    conversation_history = []
    user_message = "Hello, how are you?"

    response_a = get_assistant_response('A', conversation_history, user_message)
    response_b = get_assistant_response('B', conversation_history, user_message)

    print(f"✓ Assistant A response: {response_a[:50]}...")
    print(f"✓ Assistant B response: {response_b[:50]}...")

    print("\nAll AI service tests passed!")

if __name__ == "__main__":
    print("=" * 60)
    print("ANNOTATION SYSTEM - SETUP TEST")
    print("=" * 60)

    try:
        test_database()
        test_ai_service()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYou can now run the application with:")
        print("  streamlit run app.py")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        print("\nPlease check the error message and fix any issues.")
