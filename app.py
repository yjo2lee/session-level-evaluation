import streamlit as st
from database import (
    init_database, create_or_get_user, create_query, get_user_queries,
    create_turn_level_session, add_turn_level_turn, update_turn_selection,
    get_turn_level_session_turns, complete_turn_level_session,
    create_session_level_conversation, add_session_level_turn,
    get_session_level_conversation_turns, update_conversation_notes,
    complete_session_level_conversation, save_session_level_preference,
    get_all_users, get_all_queries_for_summary,
    get_turn_level_summary, get_session_level_summary, get_user_aggregate_stats,
    get_user_query_level_stats
)
from ai_service import get_assistant_response
import time
import pandas as pd

# Page configuration
st.set_page_config(page_title="Chat Interface", layout="wide", initial_sidebar_state="collapsed")

# Initialize database
init_database()

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'guide'
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'annotation_mode' not in st.session_state:
    st.session_state.annotation_mode = None
if 'query_id' not in st.session_state:
    st.session_state.query_id = None
if 'initial_query' not in st.session_state:
    st.session_state.initial_query = None

# Turn-level specific state
if 'turn_session_id' not in st.session_state:
    st.session_state.turn_session_id = None
if 'turn_messages' not in st.session_state:
    st.session_state.turn_messages = []
if 'turn_history_a' not in st.session_state:
    st.session_state.turn_history_a = []
if 'turn_history_b' not in st.session_state:
    st.session_state.turn_history_b = []
if 'waiting_for_selection' not in st.session_state:
    st.session_state.waiting_for_selection = False
if 'current_turn_id' not in st.session_state:
    st.session_state.current_turn_id = None

# Session-level specific state
if 'session_conversation_id' not in st.session_state:
    st.session_state.session_conversation_id = None
if 'session_messages' not in st.session_state:
    st.session_state.session_messages = []
if 'session_history' not in st.session_state:
    st.session_state.session_history = []
if 'current_assistant' not in st.session_state:
    st.session_state.current_assistant = 'A'
if 'conversation_a_id' not in st.session_state:
    st.session_state.conversation_a_id = None
if 'conversation_b_id' not in st.session_state:
    st.session_state.conversation_b_id = None
if 'show_notes_input' not in st.session_state:
    st.session_state.show_notes_input = False
if 'session_phase' not in st.session_state:
    st.session_state.session_phase = 'conversation_a'  # conversation_a, notes_a, conversation_b, notes_b, final_preference

# Confirmation state
if 'show_confirmation' not in st.session_state:
    st.session_state.show_confirmation = False
if 'confirmation_mode' not in st.session_state:
    st.session_state.confirmation_mode = None

# Track which annotation types are completed for current query
if 'turn_level_completed' not in st.session_state:
    st.session_state.turn_level_completed = False
if 'session_level_completed' not in st.session_state:
    st.session_state.session_level_completed = False

# CSS for styling
st.markdown("""
<style>
    .response-container {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .response-container:hover {
        border-color: #4CAF50;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .response-selected {
        background-color: #e8f5e9;
        border: 2px solid #4CAF50;
    }
    .response-unselected {
        background-color: #f5f5f5;
        opacity: 0.7;
    }
    .assistant-label {
        font-weight: bold;
        color: #1976D2;
        margin-bottom: 8px;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .turn-number {
        color: #666;
        font-size: 0.9em;
        margin-bottom: 5px;
    }
    .complete-button {
        position: sticky;
        top: 10px;
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

# ============= Guide Page =============

def show_guide_page():
    st.title("Welcome!")

    if st.session_state.user_id is None:
        st.write("Please enter your ID to begin:")
        user_id_input = st.text_input("Your ID:", key="user_id_input")

        if st.button("Let's start the chat!"):
            if user_id_input.strip():
                st.session_state.user_id = create_or_get_user(user_id_input.strip())
                st.rerun()
            else:
                st.error("Please enter a valid ID")
    else:
        st.write(f"Hello, {st.session_state.user_id}!")
        st.write("Please select which annotation type to start with:")
        st.info("Note: You will complete BOTH annotation types for each query. This choice determines which one you do first.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Start with Turn-by-turn", use_container_width=True):
                st.session_state.page = 'turn_level'
                st.rerun()

        with col2:
            if st.button("Start with Conversation", use_container_width=True):
                st.session_state.page = 'session_level'
                st.session_state.session_phase = 'conversation_a'
                st.rerun()

        # Secret access to summary page
        st.write("---")
        if st.checkbox("Show admin options"):
            admin_password = st.text_input("Admin password:", type="password")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Access Summary Page", use_container_width=True):
                    if admin_password == "admin123":  # Change this to a secure password
                        st.session_state.page = 'summary'
                        st.rerun()
                    else:
                        st.error("Incorrect password")

            with col2:
                # Database download button (useful for Streamlit Cloud)
                if admin_password == "admin123":
                    import os
                    from datetime import datetime
                    if os.path.exists('annotation_system.db'):
                        with open('annotation_system.db', 'rb') as f:
                            st.download_button(
                                label="📥 Download Database",
                                data=f,
                                file_name=f"annotation_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                                mime="application/octet-stream",
                                use_container_width=True
                            )

# ============= Turn-Level Annotation Page =============

def show_turn_level_page():
    # Show confirmation screen if needed
    if st.session_state.show_confirmation and st.session_state.confirmation_mode == 'turn_level':
        st.title("Turn-Level Annotation Completed!")
        st.success("Great work! Your turn-level annotations have been saved.")
        st.write("")

        # Check if session-level is also completed
        if st.session_state.session_level_completed:
            st.info("Both annotation types completed for this query!")
            st.write("Ready to start a new query?")
            col1, col2, col3 = st.columns([2, 2, 2])
            with col2:
                if st.button("New Query", type="primary", use_container_width=True):
                    # Reset everything for new query
                    st.session_state.show_confirmation = False
                    st.session_state.confirmation_mode = None
                    st.session_state.turn_level_completed = False
                    st.session_state.session_level_completed = False
                    st.session_state.query_id = None
                    st.session_state.initial_query = None
                    reset_turn_level_state()
                    reset_session_level_state()
                    st.session_state.page = 'guide'
                    st.rerun()
        else:
            st.info("Now let's do the session-level annotation for the same query.")
            st.write(f'Query: "{st.session_state.initial_query}"')
            col1, col2, col3 = st.columns([2, 2, 2])
            with col2:
                if st.button("Start Session-Level", type="primary", use_container_width=True):
                    st.session_state.show_confirmation = False
                    st.session_state.confirmation_mode = None
                    st.session_state.turn_level_completed = True
                    reset_turn_level_state()
                    st.session_state.page = 'session_level'
                    st.session_state.session_phase = 'conversation_a'
                    st.rerun()
        return

    st.title("Chat Interface")

    # Check if session has ended (10 turns)
    turn_count = len([msg for msg in st.session_state.turn_messages if msg['role'] == 'user'])

    # Auto-start with seed query if coming from session-level and no messages yet
    if turn_count == 0 and st.session_state.initial_query and st.session_state.session_level_completed:
        # Automatically process the seed query
        user_input = st.session_state.initial_query
        st.info(f"Starting turn-level annotation with seed query: \"{user_input}\"")

        # Create query if needed
        if st.session_state.query_id is None:
            st.session_state.query_id = create_query(st.session_state.user_id, user_input)

        # Create session if needed
        if st.session_state.turn_session_id is None:
            st.session_state.turn_session_id = create_turn_level_session(
                st.session_state.user_id,
                st.session_state.query_id
            )

        # Generate responses (empty history for first turn)
        response_a = get_assistant_response('A', [], user_input)
        response_b = get_assistant_response('B', [], user_input)

        # Save to database
        turn_id = add_turn_level_turn(
            st.session_state.turn_session_id,
            1,
            user_input,
            response_a,
            response_b
        )

        # Add to display
        st.session_state.turn_messages.append({
            'role': 'user',
            'content': user_input,
            'turn_number': 1
        })
        st.session_state.turn_messages.append({
            'role': 'assistant',
            'response_a': response_a,
            'response_b': response_b,
            'turn_id': turn_id,
            'user_message': user_input,
            'selected_assistant': None
        })

        st.session_state.waiting_for_selection = True
        st.rerun()
        return

    if turn_count >= 10:
        st.info("This session has reached the maximum of 10 turns. Please click 'Complete' to continue.")
        return

    # Display conversation history
    for msg in st.session_state.turn_messages:
        if msg['role'] == 'user':
            st.markdown(f"""<div class="user-message">
                <div class="turn-number">Turn {msg.get('turn_number', '')}</div>
                <strong>You:</strong> {msg['content']}
            </div>""", unsafe_allow_html=True)
        elif msg['role'] == 'assistant':
            col1, col2 = st.columns(2)

            # Determine selection state
            selected = msg.get('selected_assistant')
            is_a_selected = selected == 'A'
            is_b_selected = selected == 'B'

            with col1:
                container_class = "response-container"
                if selected:
                    container_class += " response-selected" if is_a_selected else " response-unselected"

                st.markdown(f"""<div class="{container_class}">
                    <div class="assistant-label">Assistant A</div>
                    {msg['response_a']}
                </div>""", unsafe_allow_html=True)

                if not selected and st.button("Select", key=f"select_a_{msg['turn_id']}"):
                    update_turn_selection(msg['turn_id'], 'A')
                    # Update the message in session state
                    msg['selected_assistant'] = 'A'
                    st.session_state.waiting_for_selection = False
                    st.rerun()

            with col2:
                container_class = "response-container"
                if selected:
                    container_class += " response-selected" if is_b_selected else " response-unselected"

                st.markdown(f"""<div class="{container_class}">
                    <div class="assistant-label">Assistant B</div>
                    {msg['response_b']}
                </div>""", unsafe_allow_html=True)

                if not selected and st.button("Select", key=f"select_b_{msg['turn_id']}"):
                    update_turn_selection(msg['turn_id'], 'B')
                    # Update the message in session state
                    msg['selected_assistant'] = 'B'
                    st.session_state.waiting_for_selection = False
                    st.rerun()

    # User input with Complete button right next to it
    if not st.session_state.waiting_for_selection:
        # Show complete button if there are messages
        if turn_count > 0:
            col1, col2 = st.columns([5, 1])
            with col1:
                user_input = st.chat_input("Type your message here...")
            with col2:
                st.write("")  # Spacing to align with input
                if st.button("Complete", type="primary", key="complete_button", use_container_width=True):
                    if st.session_state.turn_session_id:
                        complete_turn_level_session(st.session_state.turn_session_id)
                    # Set confirmation flag instead of calling function
                    st.session_state.show_confirmation = True
                    st.session_state.confirmation_mode = 'turn_level'
                    st.rerun()
        else:
            user_input = st.chat_input("Type your message here...")

        if user_input:
            # Create query if this is the first message
            if st.session_state.query_id is None:
                st.session_state.query_id = create_query(st.session_state.user_id, user_input)
                st.session_state.initial_query = user_input

            # Create session if needed
            if st.session_state.turn_session_id is None:
                st.session_state.turn_session_id = create_turn_level_session(
                    st.session_state.user_id,
                    st.session_state.query_id
                )

            # Generate responses
            turn_number = len([msg for msg in st.session_state.turn_messages if msg['role'] == 'user']) + 1

            # Build conversation history from previously selected responses
            shared_history = []
            for msg in st.session_state.turn_messages:
                if msg['role'] == 'user':
                    shared_history.append({
                        'role': 'user',
                        'content': msg['content']
                    })
                elif msg['role'] == 'assistant' and msg.get('selected_assistant'):
                    # Include the selected assistant's response
                    selected = msg['selected_assistant']
                    selected_response = msg['response_a'] if selected == 'A' else msg['response_b']
                    shared_history.append({
                        'role': 'assistant',
                        'content': selected_response
                    })

            response_a = get_assistant_response('A', shared_history, user_input)
            response_b = get_assistant_response('B', shared_history, user_input)

            # Save to database
            turn_id = add_turn_level_turn(
                st.session_state.turn_session_id,
                turn_number,
                user_input,
                response_a,
                response_b
            )

            # Add to display
            st.session_state.turn_messages.append({
                'role': 'user',
                'content': user_input,
                'turn_number': turn_number
            })
            st.session_state.turn_messages.append({
                'role': 'assistant',
                'response_a': response_a,
                'response_b': response_b,
                'turn_id': turn_id,
                'user_message': user_input,
                'selected_assistant': None
            })

            st.session_state.waiting_for_selection = True
            st.rerun()
    else:
        st.info("Please select one of the responses above to continue.")

# ============= Session-Level Annotation Page =============

def show_session_level_page():
    # Show confirmation screen if needed
    if st.session_state.show_confirmation and st.session_state.confirmation_mode == 'session_level':
        st.title("Session-Level Annotation Completed!")
        st.success("Great work! Your session-level annotations have been saved.")
        st.write("")

        # Check if turn-level is also completed
        if st.session_state.turn_level_completed:
            st.info("Both annotation types completed for this query!")
            st.write("Ready to start a new query?")
            col1, col2, col3 = st.columns([2, 2, 2])
            with col2:
                if st.button("New Query", type="primary", use_container_width=True):
                    # Reset everything for new query
                    st.session_state.show_confirmation = False
                    st.session_state.confirmation_mode = None
                    st.session_state.turn_level_completed = False
                    st.session_state.session_level_completed = False
                    st.session_state.query_id = None
                    st.session_state.initial_query = None
                    reset_turn_level_state()
                    reset_session_level_state()
                    st.session_state.page = 'guide'
                    st.rerun()
        else:
            st.info("Now let's do the turn-level annotation for the same query.")
            st.write(f'Query: "{st.session_state.initial_query}"')
            col1, col2, col3 = st.columns([2, 2, 2])
            with col2:
                if st.button("Start Turn-Level", type="primary", use_container_width=True):
                    st.session_state.show_confirmation = False
                    st.session_state.confirmation_mode = None
                    st.session_state.session_level_completed = True
                    reset_session_level_state()
                    st.session_state.page = 'turn_level'
                    st.rerun()
        return

    phase = st.session_state.session_phase

    if phase in ['conversation_a', 'conversation_b']:
        show_session_conversation(st.session_state.current_assistant)
    elif phase in ['notes_a', 'notes_b']:
        show_notes_input()
    elif phase == 'final_preference':
        show_final_preference()

def show_session_conversation(assistant_name):
    st.title(f"Conversation with Assistant {assistant_name}")

    turn_count = len([msg for msg in st.session_state.session_messages if msg['role'] == 'user'])
    is_last_session = (st.session_state.session_phase == 'conversation_b')

    # Auto-start with seed query if:
    # 1. No messages yet in this conversation (turn_count == 0)
    # 2. Seed query exists (initial_query is set)
    # 3. Either coming from turn-level OR switching from Assistant A to Assistant B
    should_auto_start = (
        turn_count == 0 and
        st.session_state.initial_query and
        (st.session_state.turn_level_completed or assistant_name == 'B')
    )

    if should_auto_start:
        # Automatically process the seed query
        user_input = st.session_state.initial_query
        if assistant_name == 'B':
            st.info(f"Starting conversation with Assistant B using same seed query: \"{user_input}\"")
        else:
            st.info(f"Starting conversation with seed query: \"{user_input}\"")

        # Create query if needed
        if st.session_state.query_id is None:
            st.session_state.query_id = create_query(st.session_state.user_id, user_input)

        # Create conversation
        if st.session_state.session_conversation_id is None:
            st.session_state.session_conversation_id = create_session_level_conversation(
                st.session_state.user_id,
                st.session_state.query_id,
                f"Assistant {assistant_name}"
            )
            if assistant_name == 'A':
                st.session_state.conversation_a_id = st.session_state.session_conversation_id
            else:
                st.session_state.conversation_b_id = st.session_state.session_conversation_id

        # Generate response
        response = get_assistant_response(assistant_name, st.session_state.session_history, user_input)

        # Save to database
        add_session_level_turn(
            st.session_state.session_conversation_id,
            1,
            user_input,
            response
        )

        # Update display
        st.session_state.session_messages.append({'role': 'user', 'content': user_input})
        st.session_state.session_messages.append({'role': 'assistant', 'content': response})

        # Update history
        st.session_state.session_history.append({'role': 'user', 'content': user_input})
        st.session_state.session_history.append({'role': 'assistant', 'content': response})

        st.rerun()
        return

    # Check if session has ended (10 turns)
    if turn_count >= 10:
        st.info("This session has reached the maximum of 10 turns. Please click 'Complete' to continue.")
        return

    # Display messages
    for msg in st.session_state.session_messages:
        if msg['role'] == 'user':
            st.markdown(f"""<div class="user-message">
                <strong>You:</strong> {msg['content']}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"**Assistant {assistant_name}:** {msg['content']}")

    # Chat input with Complete button right next to it
    if turn_count > 0:
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.chat_input("Type your message here...")
        with col2:
            st.write("")  # Spacing to align with input
            button_label = "Complete"
            if st.button(button_label, type="primary", key="session_complete_button", use_container_width=True):
                end_session_conversation()
                return
    else:
        user_input = st.chat_input("Type your message here...")

    if user_input:
        # Create query if this is the first message
        if st.session_state.query_id is None:
            st.session_state.query_id = create_query(st.session_state.user_id, user_input)
            st.session_state.initial_query = user_input

        # Create conversation if needed
        if st.session_state.session_conversation_id is None:
            st.session_state.session_conversation_id = create_session_level_conversation(
                st.session_state.user_id,
                st.session_state.query_id,
                f"Assistant {assistant_name}"
            )
            if assistant_name == 'A':
                st.session_state.conversation_a_id = st.session_state.session_conversation_id
            else:
                st.session_state.conversation_b_id = st.session_state.session_conversation_id

        # Generate response
        turn_number = len([msg for msg in st.session_state.session_messages if msg['role'] == 'user']) + 1
        response = get_assistant_response(assistant_name, st.session_state.session_history, user_input)

        # Save to database
        add_session_level_turn(
            st.session_state.session_conversation_id,
            turn_number,
            user_input,
            response
        )

        # Update display
        st.session_state.session_messages.append({'role': 'user', 'content': user_input})
        st.session_state.session_messages.append({'role': 'assistant', 'content': response})

        # Update history for next turn
        st.session_state.session_history.append({'role': 'user', 'content': user_input})
        st.session_state.session_history.append({'role': 'assistant', 'content': response})

        st.rerun()

def end_session_conversation():
    """End the current session conversation and move to notes."""
    if st.session_state.session_conversation_id:
        complete_session_level_conversation(st.session_state.session_conversation_id)

    # Move to notes phase
    if st.session_state.session_phase == 'conversation_a':
        st.session_state.session_phase = 'notes_a'
    elif st.session_state.session_phase == 'conversation_b':
        st.session_state.session_phase = 'notes_b'

    st.session_state.show_notes_input = True
    st.rerun()

def show_notes_input():
    """Show the notes input page after a conversation."""
    assistant_name = 'A' if st.session_state.session_phase == 'notes_a' else 'B'

    st.title(f"Conversation Summary - Assistant {assistant_name}")

    st.write("Here's the conversation you just had:")

    # Display full conversation
    for msg in st.session_state.session_messages:
        if msg['role'] == 'user':
            st.markdown(f"""<div class="user-message">
                <strong>You:</strong> {msg['content']}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"**Assistant {assistant_name}:** {msg['content']}")

    st.write("---")
    st.write("Please share any thoughts or notes about this conversation:")

    notes = st.text_area("Your notes:", height=150, key=f"notes_{assistant_name}")

    if st.button("Complete", type="primary"):
        # Save notes
        conversation_id = st.session_state.conversation_a_id if assistant_name == 'A' else st.session_state.conversation_b_id
        if notes.strip():
            update_conversation_notes(conversation_id, notes)

        # Determine next phase
        if st.session_state.session_phase == 'notes_a':
            # Show transition message and move to conversation B
            st.success("Great! Now we will start the conversation with the other assistant.")
            time.sleep(1)

            # Reset for next conversation
            st.session_state.session_phase = 'conversation_b'
            st.session_state.current_assistant = 'B'
            st.session_state.session_messages = []
            st.session_state.session_history = []
            st.session_state.session_conversation_id = None
            st.session_state.show_notes_input = False

            # Auto-start with initial query if available
            if st.session_state.initial_query:
                st.info(f"Starting conversation with: {st.session_state.initial_query}")

            st.rerun()

        elif st.session_state.session_phase == 'notes_b':
            # Move to final preference
            st.session_state.session_phase = 'final_preference'
            st.session_state.show_notes_input = False
            st.rerun()

def show_final_preference():
    """Show the final preference selection page."""
    st.title("Final Preference")

    st.write("You have now completed conversations with both assistants.")
    st.write("Which overall conversation did you prefer?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Assistant A", use_container_width=True, type="primary"):
            save_session_level_preference(
                st.session_state.user_id,
                st.session_state.query_id,
                st.session_state.conversation_a_id,
                st.session_state.conversation_b_id,
                'A'
            )
            # Mark session-level as completed and show confirmation
            st.session_state.show_confirmation = True
            st.session_state.confirmation_mode = 'session_level'
            st.rerun()

    with col2:
        if st.button("Assistant B", use_container_width=True, type="primary"):
            save_session_level_preference(
                st.session_state.user_id,
                st.session_state.query_id,
                st.session_state.conversation_a_id,
                st.session_state.conversation_b_id,
                'B'
            )
            # Mark session-level as completed and show confirmation
            st.session_state.show_confirmation = True
            st.session_state.confirmation_mode = 'session_level'
            st.rerun()

# ============= Helper Functions =============

def reset_turn_level_state():
    """Reset turn-level annotation state."""
    st.session_state.turn_session_id = None
    st.session_state.turn_messages = []
    st.session_state.turn_history_a = []
    st.session_state.turn_history_b = []
    st.session_state.waiting_for_selection = False
    st.session_state.current_turn_id = None

def reset_session_level_state():
    """Reset session-level annotation state."""
    st.session_state.session_conversation_id = None
    st.session_state.session_messages = []
    st.session_state.session_history = []
    st.session_state.current_assistant = 'A'
    st.session_state.conversation_a_id = None
    st.session_state.conversation_b_id = None
    st.session_state.show_notes_input = False
    st.session_state.session_phase = 'conversation_a'

# ============= Summary Page =============

def show_summary_page():
    st.title("Annotation Summary Dashboard")

    if st.button("← Back to Guide"):
        st.session_state.page = 'guide'
        st.rerun()

    st.write("---")

    # User and query selection
    all_users = get_all_users()
    all_queries = get_all_queries_for_summary()

    col1, col2 = st.columns(2)

    with col1:
        selected_user = st.selectbox("Select User ID:", [""] + all_users)

    with col2:
        query_options = [""] + [f"Query {q[0]}: {q[2][:50]}..." for q in all_queries if selected_user == "" or q[1] == selected_user]
        selected_query_display = st.selectbox("Select Query:", query_options)

    if selected_user and selected_query_display:
        query_id = int(selected_query_display.split(":")[0].replace("Query ", ""))

        st.write("---")

        # Turn-level summary
        st.subheader("Turn-Level Annotations")
        turn_summary = get_turn_level_summary(selected_user, query_id)

        if turn_summary['turns']:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Model A Selected", f"{turn_summary['model_a_count']} ({turn_summary['model_a_ratio']:.1%})")
            with col2:
                st.metric("Model B Selected", f"{turn_summary['model_b_count']} ({turn_summary['model_b_ratio']:.1%})")

            with st.expander("View Turn Details"):
                for turn in turn_summary['turns']:
                    st.markdown(f"### Turn {turn['turn_number']}")
                    st.markdown(f"**User:** {turn['user_message']}")

                    # 두 답변을 나란히 배치
                    resp_col1, resp_col2 = st.columns(2)

                    def render_assistant(col, name, response, selected):
                        with col:
                            if selected:
                                st.markdown(
                                    f"""
                                    <div style='background-color:#e6f4ea; border-radius:8px; padding:6px;'>
                                    <b>{name} ✓ Selected</b>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(f"<b>{name}</b>", unsafe_allow_html=True)

                            # 답변 본문
                            st.markdown(
                                f"<div style='min-height:120px;'>{response}</div>",
                                unsafe_allow_html=True
                            )

                    render_assistant(resp_col1, "Assistant A", turn["response_a"], turn["selected_assistant"] == "A")
                    render_assistant(resp_col2, "Assistant B", turn["response_b"], turn["selected_assistant"] == "B")
                    st.markdown("---")

        else:
            st.info("No turn-level annotations found.")

        st.write("---")

        # Session-level summary
        st.subheader("Session-Level Annotations")
        session_summary = get_session_level_summary(selected_user, query_id)

        if session_summary['conversations']:
            st.write(f"**Overall Preference:** Assistant {session_summary['preferred_assistant']}")

            for conv in session_summary['conversations']:
                with st.expander(f"Conversation with {conv['assistant_name']}"):
                    for turn in conv['turns']:
                        st.write(f"**Turn {turn['turn_number']}**")
                        st.write(f"User: {turn['user_message']}")
                        st.write(f"Assistant: {turn['assistant_response']}")
                        st.write("---")
                    if conv['notes']:
                        st.write("**User Notes:**")
                        st.write(conv['notes'])
        else:
            st.info("No session-level annotations found.")

        st.write("---")

        # Consistency check
        st.subheader("Query-Level Consistency")
        if turn_summary['turns'] and session_summary['preferred_assistant']:
            # turn_preferred = 'A' if turn_summary['model_a_ratio'] > turn_summary['model_b_ratio'] else 'B'
            if turn_summary['model_a_ratio'] > turn_summary['model_b_ratio']:
                turn_preferred = 'A'
            elif turn_summary['model_b_ratio'] > turn_summary['model_a_ratio']:
                turn_preferred = 'B'
            else:
                turn_preferred = 'Tie'  
            session_preferred = session_summary['preferred_assistant']

            if turn_preferred == session_preferred:
                st.success(f"✓ Consistent: Both prefer Assistant {turn_preferred}")
            else:
                st.warning(f"⚠ Inconsistent: Turn-level prefers {turn_preferred}, Session-level prefers {session_preferred}")

    st.write("---")

    # User aggregate stats
    if selected_user:
        st.subheader(f"Aggregate Statistics for {selected_user}")

        # Get per-query statistics
        stats = get_user_query_level_stats(selected_user)

        if stats['total_queries'] == 0:
            st.info(f"No completed annotations found for user '{selected_user}'.")
        else:
            # (1) Win Summary - Three cards in one row
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    label="Turn-level Query Wins",
                    value=f"A: {stats['turn_level_wins']['A']} | B: {stats['turn_level_wins']['B']} | Tie: {stats['turn_level_wins']['tie']}",
                    help="Number of seed queries won by each model based on per-turn majority votes. Tie indicates equal number of turn-level votes for both models."
                )

            with col2:
                st.metric(
                    label="Session-level Preferences",
                    value=f"A: {stats['session_level_wins']['A']} | B: {stats['session_level_wins']['B']}",
                    help="Number of seed queries won by each model based on session-level judgments"
                )

            with col3:
                consistency_decimal = stats['consistency_rate'] / 100
                st.metric(
                    label="Preference Consistency",
                    value=f"{consistency_decimal:.2f}",
                    help="A 0-1 metric indicating how consistently the user preferred the same model across turn-level and session-level annotations (includes all queries with both annotations)"
                )

            st.write("")  # Add spacing

            # (2) Visual Summary Charts - Two bar charts side by side
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.write("**Turn-level Winners per Seed Query**")

                # Create bar chart data including ties
                turn_data = pd.DataFrame({
                    'Model': ['Model A', 'Model B', 'Tie'],
                    'Number of Queries Won': [stats['turn_level_wins']['A'], stats['turn_level_wins']['B'], stats['turn_level_wins']['tie']]
                })

                # Display bar chart
                st.bar_chart(turn_data.set_index('Model'), height=300)

                # Show counts below chart
                st.caption(f"Model A: {stats['turn_level_wins']['A']} queries | Model B: {stats['turn_level_wins']['B']} queries | Tie: {stats['turn_level_wins']['tie']} queries")

            with chart_col2:
                st.write("**Session-level Winners per Seed Query**")

                # Create bar chart data
                session_data = pd.DataFrame({
                    'Model': ['Model A', 'Model B'],
                    'Number of Queries Won': [stats['session_level_wins']['A'], stats['session_level_wins']['B']]
                })

                # Display bar chart
                st.bar_chart(session_data.set_index('Model'), height=300)

                # Show counts below chart
                st.caption(f"Model A: {stats['session_level_wins']['A']} queries | Model B: {stats['session_level_wins']['B']} queries")

# ============= Main App Router =============

def main():
    page = st.session_state.page

    if page == 'guide':
        show_guide_page()
    elif page == 'turn_level':
        show_turn_level_page()
    elif page == 'session_level':
        show_session_level_page()
    elif page == 'summary':
        show_summary_page()

if __name__ == "__main__":
    main()
