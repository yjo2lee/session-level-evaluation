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
from pilot_config import PILOT_QUERIES, PILOT_ASSIGNMENTS
import time
import pandas as pd
import random

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
if 'session_order' not in st.session_state:
    st.session_state.session_order = None  # Will be set when session-level starts: 'A_first' or 'B_first'
# Store conversation histories and notes for final comparison
if 'session_1_messages' not in st.session_state:
    st.session_state.session_1_messages = []
if 'session_2_messages' not in st.session_state:
    st.session_state.session_2_messages = []
if 'session_1_notes' not in st.session_state:
    st.session_state.session_1_notes = ""
if 'session_2_notes' not in st.session_state:
    st.session_state.session_2_notes = ""

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

# Pilot study mode state
if 'pilot_mode' not in st.session_state:
    st.session_state.pilot_mode = False
if 'pilot_current_session' not in st.session_state:
    st.session_state.pilot_current_session = 1  # 1-4
if 'pilot_phase' not in st.session_state:
    st.session_state.pilot_phase = 'conversation'  # conversation, notes, pair_preference, continue_prompt, completed
if 'pilot_messages' not in st.session_state:
    st.session_state.pilot_messages = []
if 'pilot_history' not in st.session_state:
    st.session_state.pilot_history = []
if 'pilot_conversation_id' not in st.session_state:
    st.session_state.pilot_conversation_id = None
# Store data for pair comparisons
if 'pilot_pair_1_session_1' not in st.session_state:
    st.session_state.pilot_pair_1_session_1 = {'messages': [], 'notes': '', 'assistant': None, 'query': None}
if 'pilot_pair_1_session_2' not in st.session_state:
    st.session_state.pilot_pair_1_session_2 = {'messages': [], 'notes': '', 'assistant': None, 'query': None}
if 'pilot_pair_2_session_1' not in st.session_state:
    st.session_state.pilot_pair_2_session_1 = {'messages': [], 'notes': '', 'assistant': None, 'query': None}
if 'pilot_pair_2_session_2' not in st.session_state:
    st.session_state.pilot_pair_2_session_2 = {'messages': [], 'notes': '', 'assistant': None, 'query': None}
# Store survey responses for each pair
if 'pilot_pair_1_survey' not in st.session_state:
    st.session_state.pilot_pair_1_survey = {}
if 'pilot_pair_2_survey' not in st.session_state:
    st.session_state.pilot_pair_2_survey = {}

# Store all pilot study results for analysis (persists across sessions)
if 'pilot_all_results' not in st.session_state:
    st.session_state.pilot_all_results = {}  # {participant_id: {pair_1: {...}, pair_2: {...}}}

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

        # Pilot study button
        st.write("")
        st.divider()
        st.write("**Pilot Study Mode:**")
        
        # Check if user is a valid pilot participant
        user_id = st.session_state.user_id
        if user_id in PILOT_ASSIGNMENTS:
            st.success(f"You are registered as pilot participant {user_id}.")
            if st.button("🧪 Single Query (Pilot Study)", use_container_width=True, type="primary"):
                st.session_state.pilot_mode = True
                st.session_state.pilot_current_session = 1
                st.session_state.pilot_phase = 'conversation'
                st.session_state.page = 'pilot'
                st.rerun()
        else:
            st.warning("Pilot study mode is only available for registered participants (P1-P4).")

        # Secret access to summary page
        st.write("---")
        if st.checkbox("Show admin options"):
            admin_password = st.text_input("Admin password:", type="password")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Access Summary Page", use_container_width=True):
                    if admin_password == "admin123":  # Change this to a secure password
                        st.session_state.page = 'summary'
                        st.rerun()
                    else:
                        st.error("Incorrect password")

            with col2:
                if st.button("📊 Pilot Analysis", use_container_width=True):
                    if admin_password == "admin123":
                        st.session_state.page = 'pilot_analysis'
                        st.rerun()
                    else:
                        st.error("Incorrect password")

            with col3:
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

        # Add to display with randomized order
        # Randomly decide which response goes to which position
        show_a_first = random.choice([True, False])

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
            'selected_assistant': None,
            'show_a_first': show_a_first  # Track display order
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

            # Get randomization order (default to True for backwards compatibility)
            show_a_first = msg.get('show_a_first', True)

            # Determine which response goes in which position
            if show_a_first:
                left_response = msg['response_a']
                left_assistant = 'A'
                right_response = msg['response_b']
                right_assistant = 'B'
            else:
                left_response = msg['response_b']
                left_assistant = 'B'
                right_response = msg['response_a']
                right_assistant = 'A'

            # Determine selection state
            selected = msg.get('selected_assistant')
            is_left_selected = selected == left_assistant
            is_right_selected = selected == right_assistant

            with col1:
                container_class = "response-container"
                if selected:
                    container_class += " response-selected" if is_left_selected else " response-unselected"

                st.markdown(f"""<div class="{container_class}">
                    <div class="assistant-label">Response 1</div>
                    {left_response}
                </div>""", unsafe_allow_html=True)

                if not selected and st.button("Select", key=f"select_left_{msg['turn_id']}"):
                    update_turn_selection(msg['turn_id'], left_assistant)
                    # Update the message in session state
                    msg['selected_assistant'] = left_assistant
                    st.session_state.waiting_for_selection = False
                    st.rerun()

            with col2:
                container_class = "response-container"
                if selected:
                    container_class += " response-selected" if is_right_selected else " response-unselected"

                st.markdown(f"""<div class="{container_class}">
                    <div class="assistant-label">Response 2</div>
                    {right_response}
                </div>""", unsafe_allow_html=True)

                if not selected and st.button("Select", key=f"select_right_{msg['turn_id']}"):
                    update_turn_selection(msg['turn_id'], right_assistant)
                    # Update the message in session state
                    msg['selected_assistant'] = right_assistant
                    st.session_state.waiting_for_selection = False
                    st.rerun()

    # User input area
    if not st.session_state.waiting_for_selection:
        user_input = st.chat_input("Type your message here...")
        
        # Complete button - visually separated from chat input
        if turn_count > 0:
            st.write("")  # Add spacing
            # st.write("")  # Add more spacing
            st.divider()
            
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if st.button("🏁 End Session", type="secondary", key="complete_button", use_container_width=True):
                    if st.session_state.turn_session_id:
                        complete_turn_level_session(st.session_state.turn_session_id)
                    # Set confirmation flag instead of calling function
                    st.session_state.show_confirmation = True
                    st.session_state.confirmation_mode = 'turn_level'
                    st.rerun()

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

            # Add to display with randomized order
            # Randomly decide which response goes to which position
            show_a_first = random.choice([True, False])

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
                'selected_assistant': None,
                'show_a_first': show_a_first  # Track display order
            })

            st.session_state.waiting_for_selection = True
            st.rerun()
    else:
        st.info("Please select one of the responses above to continue.")

# ============= Session-Level Annotation Page =============

def show_session_level_page():
    # Initialize randomized session order if not already set
    if st.session_state.session_order is None:
        st.session_state.session_order = random.choice(['A_first', 'B_first'])
        # Set initial assistant based on randomized order
        if st.session_state.session_order == 'A_first':
            st.session_state.current_assistant = 'A'
        else:
            st.session_state.current_assistant = 'B'

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
    # Determine session number based on phase
    session_number = 1 if st.session_state.session_phase in ['conversation_a', 'notes_a'] else 2
    st.title(f"Conversation - Session {session_number}")

    turn_count = len([msg for msg in st.session_state.session_messages if msg['role'] == 'user'])
    is_last_session = (st.session_state.session_phase == 'conversation_b')

    # Auto-start with seed query if:
    # 1. No messages yet in this conversation (turn_count == 0)
    # 2. Seed query exists (initial_query is set)
    # 3. Either coming from turn-level OR switching to Session 2
    should_auto_start = (
        turn_count == 0 and
        st.session_state.initial_query and
        (st.session_state.turn_level_completed or session_number == 2)
    )

    if should_auto_start:
        # Automatically process the seed query
        user_input = st.session_state.initial_query
        if session_number == 2:
            st.info(f"Starting Session {session_number} with the same seed query: \"{user_input}\"")
        else:
            st.info(f"Starting Session {session_number} with seed query: \"{user_input}\"")

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
            st.markdown(f"**Assistant:** {msg['content']}")

    # Chat input area
    user_input = st.chat_input("Type your message here...")
    
    # Complete button - visually separated from chat input
    if turn_count > 0:
        st.write("")  # Add spacing
        # st.write("")  # Add more spacing
        st.divider()
        # st.markdown("##### Ready to finish this conversation?")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🏁 End Session", type="secondary", key="session_complete_button", use_container_width=True):
                end_session_conversation()
                return

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
    session_number = 1 if st.session_state.session_phase == 'notes_a' else 2

    st.title(f"Conversation Summary - Session {session_number}")

    st.write("Here's the conversation you just had:")

    # Display full conversation
    for msg in st.session_state.session_messages:
        if msg['role'] == 'user':
            st.markdown(f"""<div class="user-message">
                <strong>You:</strong> {msg['content']}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"**Assistant:** {msg['content']}")

    st.write("---")
    st.write("Please share any thoughts or notes about this conversation:")

    notes = st.text_area("Your notes:", height=150, key=f"notes_{session_number}")

    if st.button("Complete", type="primary"):
        # Save notes
        conversation_id = st.session_state.conversation_a_id if assistant_name == 'A' else st.session_state.conversation_b_id
        if notes.strip():
            update_conversation_notes(conversation_id, notes)

        # Determine next phase
        if st.session_state.session_phase == 'notes_a':
            # Store session 1 messages and notes for final comparison
            st.session_state.session_1_messages = st.session_state.session_messages.copy()
            st.session_state.session_1_notes = notes.strip()
            
            # Show transition message and move to conversation B
            st.success("Great! Now we will start Session 2.")
            time.sleep(1)

            # Reset for next conversation
            st.session_state.session_phase = 'conversation_b'
            # Set second assistant based on randomized order
            if st.session_state.session_order == 'A_first':
                st.session_state.current_assistant = 'B'
            else:
                st.session_state.current_assistant = 'A'
            st.session_state.session_messages = []
            st.session_state.session_history = []
            st.session_state.session_conversation_id = None
            st.session_state.show_notes_input = False

            # Auto-start with initial query if available
            if st.session_state.initial_query:
                st.info(f"Starting Session 2 with: {st.session_state.initial_query}")

            st.rerun()

        elif st.session_state.session_phase == 'notes_b':
            # Store session 2 messages and notes for final comparison
            st.session_state.session_2_messages = st.session_state.session_messages.copy()
            st.session_state.session_2_notes = notes.strip()
            
            # Move to final preference
            st.session_state.session_phase = 'final_preference'
            st.session_state.show_notes_input = False
            st.rerun()

def show_final_preference():
    """Show the final preference selection page with side-by-side conversation comparison."""
    st.title("Final Preference")

    st.write("You have now completed both conversation sessions. Review them below and select your preferred one.")
    
    # Determine which session corresponds to which assistant
    if st.session_state.session_order == 'A_first':
        session_1_assistant = 'A'
        session_2_assistant = 'B'
    else:
        session_1_assistant = 'B'
        session_2_assistant = 'A'

    st.divider()
    
    # Display both conversations side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💬 Session 1")
        with st.container(height=350):
            for msg in st.session_state.session_1_messages:
                if msg['role'] == 'user':
                    st.markdown(f"""<div style="background-color: #e3f2fd; padding: 8px; border-radius: 8px; margin: 5px 0;">
                        <strong>You:</strong> {msg['content']}
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div style="background-color: #f5f5f5; padding: 8px; border-radius: 8px; margin: 5px 0;">
                        <strong>Assistant:</strong> {msg['content']}
                    </div>""", unsafe_allow_html=True)
        
        # Display notes for Session 1
        st.markdown("**📝 Your notes:**")
        if st.session_state.session_1_notes:
            st.markdown(f"""<div style="background-color: #fff3e0; padding: 10px; border-radius: 8px; border-left: 4px solid #ff9800; font-style: italic;">
                {st.session_state.session_1_notes}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("_No notes recorded_")
    
    with col2:
        st.markdown("### 💬 Session 2")
        with st.container(height=350):
            for msg in st.session_state.session_2_messages:
                if msg['role'] == 'user':
                    st.markdown(f"""<div style="background-color: #e3f2fd; padding: 8px; border-radius: 8px; margin: 5px 0;">
                        <strong>You:</strong> {msg['content']}
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div style="background-color: #f5f5f5; padding: 8px; border-radius: 8px; margin: 5px 0;">
                        <strong>Assistant:</strong> {msg['content']}
                    </div>""", unsafe_allow_html=True)
        
        # Display notes for Session 2
        st.markdown("**📝 Your notes:**")
        if st.session_state.session_2_notes:
            st.markdown(f"""<div style="background-color: #fff3e0; padding: 10px; border-radius: 8px; border-left: 4px solid #ff9800; font-style: italic;">
                {st.session_state.session_2_notes}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("_No notes recorded_")
    
    st.divider()
    st.markdown("### Which conversation did you prefer?")
    
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        if st.button("⭐ Prefer Session 1", use_container_width=True, type="primary"):
            save_session_level_preference(
                st.session_state.user_id,
                st.session_state.query_id,
                st.session_state.conversation_a_id,
                st.session_state.conversation_b_id,
                session_1_assistant  # Map Session 1 to actual assistant
            )
            # Mark session-level as completed and show confirmation
            st.session_state.show_confirmation = True
            st.session_state.confirmation_mode = 'session_level'
            st.rerun()

    with btn_col2:
        if st.button("⭐ Prefer Session 2", use_container_width=True, type="primary"):
            save_session_level_preference(
                st.session_state.user_id,
                st.session_state.query_id,
                st.session_state.conversation_a_id,
                st.session_state.conversation_b_id,
                session_2_assistant  # Map Session 2 to actual assistant
            )
            # Mark session-level as completed and show confirmation
            st.session_state.show_confirmation = True
            st.session_state.confirmation_mode = 'session_level'
            st.rerun()

# ============= Pilot Study Page =============

def show_pilot_page():
    """Main router for pilot study mode."""
    phase = st.session_state.pilot_phase
    
    if phase == 'conversation':
        show_pilot_conversation()
    elif phase == 'notes':
        show_pilot_notes()
    elif phase == 'pair_preference':
        show_pilot_pair_preference()
    elif phase == 'continue_prompt':
        show_pilot_continue_prompt()
    elif phase == 'completed':
        show_pilot_completed()

def get_current_pilot_assignment():
    """Get the current assignment for the pilot participant."""
    user_id = st.session_state.user_id
    current_session = st.session_state.pilot_current_session
    
    if user_id not in PILOT_ASSIGNMENTS:
        return None
    
    assignments = PILOT_ASSIGNMENTS[user_id]
    for assignment in assignments:
        if assignment['session'] == current_session:
            return assignment
    return None

def show_pilot_conversation():
    """Show the conversation page for pilot study."""
    assignment = get_current_pilot_assignment()
    if not assignment:
        st.error("Invalid pilot assignment. Please contact the administrator.")
        return
    
    session_num = assignment['session']
    query_id = assignment['query']
    assistant = assignment['assistant']
    pair_num = assignment['pair']
    query_text = PILOT_QUERIES[query_id]
    
    st.title(f"Session {session_num} of 4")
    st.caption(f"Comparison Pair {pair_num} • Query: {query_id}")
    
    turn_count = len([msg for msg in st.session_state.pilot_messages if msg['role'] == 'user'])
    
    # Auto-start with the predefined query if no messages yet
    if turn_count == 0:
        # Create query in database
        if st.session_state.query_id is None:
            st.session_state.query_id = create_query(st.session_state.user_id, query_text)
            st.session_state.initial_query = query_text
        
        # Create conversation in database
        if st.session_state.pilot_conversation_id is None:
            st.session_state.pilot_conversation_id = create_session_level_conversation(
                st.session_state.user_id,
                st.session_state.query_id,
                f"Pilot Assistant {assistant}"
            )
        
        # Generate first response
        response = get_assistant_response(assistant, [], query_text)
        
        # Save to database
        add_session_level_turn(
            st.session_state.pilot_conversation_id,
            1,
            query_text,
            response
        )
        
        # Update display
        st.session_state.pilot_messages.append({'role': 'user', 'content': query_text})
        st.session_state.pilot_messages.append({'role': 'assistant', 'content': response})
        st.session_state.pilot_history.append({'role': 'user', 'content': query_text})
        st.session_state.pilot_history.append({'role': 'assistant', 'content': response})
        
        st.rerun()
        return
    
    # Check if session has ended (10 turns)
    if turn_count >= 10:
        st.info("This session has reached the maximum of 10 turns. Please click 'End Session' to continue.")
    
    # Display messages
    for msg in st.session_state.pilot_messages:
        if msg['role'] == 'user':
            st.markdown(f"""<div class="user-message">
                <strong>You:</strong> {msg['content']}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"**Assistant:** {msg['content']}")
    
    # Chat input area
    if turn_count < 10:
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Generate response
            turn_number = turn_count + 1
            response = get_assistant_response(assistant, st.session_state.pilot_history, user_input)
            
            # Save to database
            add_session_level_turn(
                st.session_state.pilot_conversation_id,
                turn_number,
                user_input,
                response
            )
            
            # Update display
            st.session_state.pilot_messages.append({'role': 'user', 'content': user_input})
            st.session_state.pilot_messages.append({'role': 'assistant', 'content': response})
            st.session_state.pilot_history.append({'role': 'user', 'content': user_input})
            st.session_state.pilot_history.append({'role': 'assistant', 'content': response})
            
            st.rerun()
    
    # End session button
    if turn_count > 0:
        st.write("")
        st.divider()
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🏁 End Session", type="secondary", key="pilot_end_session", use_container_width=True):
                # Complete conversation in database
                if st.session_state.pilot_conversation_id:
                    complete_session_level_conversation(st.session_state.pilot_conversation_id)
                
                # Move to notes phase
                st.session_state.pilot_phase = 'notes'
                st.rerun()

def show_pilot_notes():
    """Show the notes input page for pilot study."""
    assignment = get_current_pilot_assignment()
    if not assignment:
        st.error("Invalid pilot assignment.")
        return
    
    session_num = assignment['session']
    
    st.title(f"Session {session_num} Summary")
    
    st.write("Here's the conversation you just had:")
    
    # Display full conversation
    with st.container(height=300):
        for msg in st.session_state.pilot_messages:
            if msg['role'] == 'user':
                st.markdown(f"""<div style="background-color: #e3f2fd; padding: 8px; border-radius: 8px; margin: 5px 0;">
                    <strong>You:</strong> {msg['content']}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style="background-color: #f5f5f5; padding: 8px; border-radius: 8px; margin: 5px 0;">
                    <strong>Assistant:</strong> {msg['content']}
                </div>""", unsafe_allow_html=True)
    
    st.write("---")
    st.write("Please share any thoughts or notes about this conversation:")
    
    notes = st.text_area("Your notes:", height=150, key=f"pilot_notes_{session_num}")
    
    if st.button("Continue", type="primary"):
        # Save notes to database
        if notes.strip() and st.session_state.pilot_conversation_id:
            update_conversation_notes(st.session_state.pilot_conversation_id, notes)
        
        # Store session data for pair comparison
        session_data = {
            'messages': st.session_state.pilot_messages.copy(),
            'notes': notes.strip(),
            'assistant': assignment['assistant'],
            'query': assignment['query']
        }
        
        current_session = st.session_state.pilot_current_session
        if current_session == 1:
            st.session_state.pilot_pair_1_session_1 = session_data
        elif current_session == 2:
            st.session_state.pilot_pair_1_session_2 = session_data
        elif current_session == 3:
            st.session_state.pilot_pair_2_session_1 = session_data
        elif current_session == 4:
            st.session_state.pilot_pair_2_session_2 = session_data
        
        # Determine next phase
        if current_session in [2, 4]:
            # After sessions 2 and 4, show pair preference
            st.session_state.pilot_phase = 'pair_preference'
        else:
            # After sessions 1 and 3, continue to next session
            st.session_state.pilot_phase = 'continue_prompt'
        
        st.rerun()

def show_pilot_pair_preference():
    """Show the survey/feedback page after completing a comparison pair."""
    current_session = st.session_state.pilot_current_session
    
    if current_session == 2:
        pair_num = 1
        session_1_data = st.session_state.pilot_pair_1_session_1
        session_2_data = st.session_state.pilot_pair_1_session_2
    else:  # session 4
        pair_num = 2
        session_1_data = st.session_state.pilot_pair_2_session_1
        session_2_data = st.session_state.pilot_pair_2_session_2
    
    # Map generic labels to actual assistants
    # "Assistant 1" = first session's assistant, "Assistant 2" = second session's assistant
    assistant_1_actual = session_1_data['assistant']  # A or B
    assistant_2_actual = session_2_data['assistant']  # A or B
    
    st.title(f"Comparison Pair {pair_num} - Feedback Survey")
    st.write("You have completed two sessions. Please review the conversations and answer the survey questions below.")
    
    # Display both conversations side by side
    st.markdown("---")
    st.markdown("### 📋 Review Your Conversations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💬 Assistant 1")
        st.caption(f"Query: {session_1_data['query']}")
        with st.container(height=250):
            for msg in session_1_data['messages']:
                if msg['role'] == 'user':
                    st.markdown(f"""<div style="background-color: #e3f2fd; padding: 8px; border-radius: 8px; margin: 5px 0;">
                        <strong>You:</strong> {msg['content']}
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div style="background-color: #f5f5f5; padding: 8px; border-radius: 8px; margin: 5px 0;">
                        <strong>Assistant:</strong> {msg['content']}
                    </div>""", unsafe_allow_html=True)
        
        if session_1_data['notes']:
            with st.expander("📝 Your notes"):
                st.markdown(f"_{session_1_data['notes']}_")
    
    with col2:
        st.markdown("#### 💬 Assistant 2")
        st.caption(f"Query: {session_2_data['query']}")
        with st.container(height=250):
            for msg in session_2_data['messages']:
                if msg['role'] == 'user':
                    st.markdown(f"""<div style="background-color: #e3f2fd; padding: 8px; border-radius: 8px; margin: 5px 0;">
                        <strong>You:</strong> {msg['content']}
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div style="background-color: #f5f5f5; padding: 8px; border-radius: 8px; margin: 5px 0;">
                        <strong>Assistant:</strong> {msg['content']}
                    </div>""", unsafe_allow_html=True)
        
        if session_2_data['notes']:
            with st.expander("📝 Your notes"):
                st.markdown(f"_{session_2_data['notes']}_")
    
    # Survey Form
    st.markdown("---")
    st.markdown("### 📝 Survey Questions")
    
    with st.form(key=f"pilot_survey_pair_{pair_num}"):
        # Q1: Overall Preference
        st.markdown("#### 1. Overall Preference")
        q1_preference = st.radio(
            "Overall, which assistant was more helpful?",
            options=["Assistant 1", "Assistant 2"],
            index=None,
            key=f"q1_pref_{pair_num}",
            horizontal=True
        )
        q1_explanation = st.text_area(
            "Please briefly explain your choice:",
            height=100,
            key=f"q1_explain_{pair_num}"
        )
        
        st.markdown("---")
        
        # Q2: Reasons for Preference
        st.markdown("#### 2. Reasons for Preference")
        st.write("Why did you prefer that assistant? (Select all that apply)")
        
        preference_reasons = [
            "The responses were easy to understand",
            "I could quickly get the information I wanted",
            "The answer was specific and actionable",
            "The assistant felt personalized to my needs",
            "The conversation flow felt more natural",
            "The response was concise without unnecessary details",
            "The assistant reflected what I had already said",
            "It was easy to know what to do next"
        ]
        
        q2_selections = []
        cols = st.columns(2)
        for i, reason in enumerate(preference_reasons):
            with cols[i % 2]:
                if st.checkbox(reason, key=f"q2_reason_{pair_num}_{i}"):
                    q2_selections.append(reason)
        
        q2_other = st.text_input("Other (please describe):", key=f"q2_other_{pair_num}")
        
        st.markdown("---")
        
        # Q3: Usefulness for Trip Planning
        st.markdown("#### 3. Usefulness for Trip Planning")
        q3_useful = st.radio(
            "Which assistant felt more useful for *actually planning your trip*?",
            options=["Assistant 1", "Assistant 2"],
            index=None,
            key=f"q3_useful_{pair_num}",
            horizontal=True
        )
        
        st.markdown("---")
        
        # Q4: Actionability
        st.markdown("#### 4. Actionability")
        q4_actionable = st.radio(
            "Which assistant provided more actionable information?",
            options=["Assistant 1", "Assistant 2"],
            index=None,
            key=f"q4_action_{pair_num}",
            horizontal=True
        )
        
        st.markdown("---")
        
        # Q5: Improvement Suggestions (split into two)
        st.markdown("#### 5. Improvement Suggestions")
        
        q5_col1, q5_col2 = st.columns(2)
        with q5_col1:
            q5_improve_1 = st.text_area(
                "If you could improve Assistant 1, what would you change?",
                height=120,
                key=f"q5_improve_1_{pair_num}",
                placeholder="Suggestions for Assistant 1..."
            )
        
        with q5_col2:
            q5_improve_2 = st.text_area(
                "If you could improve Assistant 2, what would you change?",
                height=120,
                key=f"q5_improve_2_{pair_num}",
                placeholder="Suggestions for Assistant 2..."
            )
        
        st.markdown("---")
        
        # Submit button
        submitted = st.form_submit_button("Submit Feedback", type="primary", use_container_width=True)
        
        if submitted:
            # Validate required fields
            if not q1_preference:
                st.error("Please select your overall preference (Question 1).")
            elif not q3_useful:
                st.error("Please answer Question 3 (Usefulness for Trip Planning).")
            elif not q4_actionable:
                st.error("Please answer Question 4 (Actionability).")
            else:
                # Map UI labels to actual assistant identifiers
                def map_to_actual_assistant(ui_choice):
                    if ui_choice == "Assistant 1":
                        return assistant_1_actual
                    elif ui_choice == "Assistant 2":
                        return assistant_2_actual
                    return None
                
                # Compile all reasons including "Other"
                all_reasons = q2_selections.copy()
                if q2_other.strip():
                    all_reasons.append(f"Other: {q2_other.strip()}")
                
                # Store survey responses with actual assistant identifiers
                survey_data = {
                    'q1_preference': map_to_actual_assistant(q1_preference),
                    'q1_preference_ui': q1_preference,
                    'q1_explanation': q1_explanation.strip(),
                    'q2_reasons': all_reasons,
                    'q3_useful': map_to_actual_assistant(q3_useful),
                    'q3_useful_ui': q3_useful,
                    'q4_actionable': map_to_actual_assistant(q4_actionable),
                    'q4_actionable_ui': q4_actionable,
                    # Q5 improvements mapped to actual assistants
                    f'q5_improvements_{assistant_1_actual}': q5_improve_1.strip(),
                    f'q5_improvements_{assistant_2_actual}': q5_improve_2.strip(),
                    'q5_improvements_assistant_1_ui': q5_improve_1.strip(),
                    'q5_improvements_assistant_2_ui': q5_improve_2.strip(),
                    'assistant_1_actual': assistant_1_actual,
                    'assistant_2_actual': assistant_2_actual
                }
                
                # Save to session state
                if pair_num == 1:
                    st.session_state.pilot_pair_1_survey = survey_data
                else:
                    st.session_state.pilot_pair_2_survey = survey_data
                
                # Save overall preference for backward compatibility
                st.session_state[f'pilot_pair_{pair_num}_preference'] = map_to_actual_assistant(q1_preference)
                
                # Move to continue prompt or completion
                if current_session == 2:
                    st.session_state.pilot_phase = 'continue_prompt'
                else:
                    st.session_state.pilot_phase = 'completed'
                st.rerun()

def show_pilot_continue_prompt():
    """Show the continue prompt between sessions."""
    current_session = st.session_state.pilot_current_session
    next_session = current_session + 1
    
    if current_session == 1:
        st.title("Session 1 Complete!")
        st.success("Great work! You've completed the first session.")
        st.write("")
        st.info(f"Next up: Session 2 (still in Comparison Pair 1)")
    elif current_session == 2:
        st.title("Comparison Pair 1 Complete!")
        st.success("You've completed the first comparison pair and submitted your preference.")
        st.write("")
        st.info(f"Next up: Session 3 (starting Comparison Pair 2)")
    elif current_session == 3:
        st.title("Session 3 Complete!")
        st.success("Great work! You've completed session 3.")
        st.write("")
        st.info(f"Next up: Session 4 (final session in Comparison Pair 2)")
    
    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Proceed to Next Session", type="primary", use_container_width=True):
            # Reset for next session
            st.session_state.pilot_current_session = next_session
            st.session_state.pilot_phase = 'conversation'
            st.session_state.pilot_messages = []
            st.session_state.pilot_history = []
            st.session_state.pilot_conversation_id = None
            st.session_state.query_id = None
            st.session_state.initial_query = None
            st.rerun()

def show_pilot_completed():
    """Show the completion page for pilot study."""
    # Save results to aggregated storage for analysis
    user_id = st.session_state.user_id
    if user_id and user_id not in st.session_state.pilot_all_results:
        st.session_state.pilot_all_results[user_id] = {
            'pair_1': {
                'survey': st.session_state.get('pilot_pair_1_survey', {}),
                'session_1': st.session_state.get('pilot_pair_1_session_1', {}),
                'session_2': st.session_state.get('pilot_pair_1_session_2', {})
            },
            'pair_2': {
                'survey': st.session_state.get('pilot_pair_2_survey', {}),
                'session_1': st.session_state.get('pilot_pair_2_session_1', {}),
                'session_2': st.session_state.get('pilot_pair_2_session_2', {})
            }
        }
    
    st.title("🎉 Pilot Study Complete!")
    st.balloons()
    
    st.success("Congratulations! You have completed all 4 sessions of the pilot study.")
    
    st.write("")
    st.markdown("### Your Feedback Summary")
    
    # Display summary for each pair
    for pair_num in [1, 2]:
        survey_key = f'pilot_pair_{pair_num}_survey'
        survey_data = st.session_state.get(survey_key, {})
        
        with st.expander(f"📊 Comparison Pair {pair_num} Summary", expanded=True):
            if survey_data:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Overall Preference:** Assistant {survey_data.get('q1_preference', 'N/A')}")
                    st.markdown(f"**Most Useful:** Assistant {survey_data.get('q3_useful', 'N/A')}")
                with col2:
                    st.markdown(f"**Most Actionable:** Assistant {survey_data.get('q4_actionable', 'N/A')}")
                
                if survey_data.get('q1_explanation'):
                    st.markdown("**Your Explanation:**")
                    st.info(survey_data['q1_explanation'])
                
                if survey_data.get('q2_reasons'):
                    st.markdown("**Reasons for Preference:**")
                    for reason in survey_data['q2_reasons']:
                        st.markdown(f"- {reason}")
                
                # Display improvement suggestions for each assistant
                imp_col1, imp_col2 = st.columns(2)
                with imp_col1:
                    st.markdown("**Suggestions for Assistant A:**")
                    if survey_data.get('q5_improvements_A'):
                        st.info(survey_data['q5_improvements_A'])
                    else:
                        st.caption("_No suggestions_")
                with imp_col2:
                    st.markdown("**Suggestions for Assistant B:**")
                    if survey_data.get('q5_improvements_B'):
                        st.info(survey_data['q5_improvements_B'])
                    else:
                        st.caption("_No suggestions_")
            else:
                st.write("No survey data recorded.")
    
    st.write("")
    st.write("Thank you for participating in the pilot study!")
    
    st.write("")
    if st.button("← Return to Home", type="primary"):
        reset_pilot_state()
        st.session_state.page = 'guide'
        st.rerun()

def reset_pilot_state():
    """Reset all pilot study state."""
    st.session_state.pilot_mode = False
    st.session_state.pilot_current_session = 1
    st.session_state.pilot_phase = 'conversation'
    st.session_state.pilot_messages = []
    st.session_state.pilot_history = []
    st.session_state.pilot_conversation_id = None
    st.session_state.pilot_pair_1_session_1 = {'messages': [], 'notes': '', 'assistant': None, 'query': None}
    st.session_state.pilot_pair_1_session_2 = {'messages': [], 'notes': '', 'assistant': None, 'query': None}
    st.session_state.pilot_pair_2_session_1 = {'messages': [], 'notes': '', 'assistant': None, 'query': None}
    st.session_state.pilot_pair_2_session_2 = {'messages': [], 'notes': '', 'assistant': None, 'query': None}
    st.session_state.pilot_pair_1_survey = {}
    st.session_state.pilot_pair_2_survey = {}
    if 'pilot_pair_1_preference' in st.session_state:
        del st.session_state['pilot_pair_1_preference']
    if 'pilot_pair_2_preference' in st.session_state:
        del st.session_state['pilot_pair_2_preference']
    st.session_state.query_id = None
    st.session_state.initial_query = None

# ============= Pilot Analysis Page =============

def show_pilot_analysis_page():
    """Show the analysis page for pilot study results."""
    st.title("📊 Pilot Study Analysis")
    
    if st.button("← Back to Home"):
        st.session_state.page = 'guide'
        st.rerun()
    
    # Get all pilot results
    all_results = st.session_state.get('pilot_all_results', {})
    
    # Tab navigation
    tab1, tab2 = st.tabs(["📈 Summary View", "🔍 Detail View"])
    
    with tab1:
        show_pilot_summary_view(all_results)
    
    with tab2:
        show_pilot_detail_view(all_results)

def show_pilot_summary_view(all_results):
    """Show the summary/aggregate view of pilot results."""
    
    if not all_results:
        st.info("No pilot study results available yet. Complete some pilot sessions first.")
        
        # Option to load demo data
        if st.button("Load Demo Data for Testing"):
            load_demo_pilot_data()
            st.rerun()
        return
    
    st.markdown("---")
    
    # 1. Preference Consistency Analysis
    st.markdown("### 1. Preference Consistency Analysis")
    
    # Within-Subject Consistency
    st.markdown("#### Within-Subject Consistency")
    
    consistency_data = []
    for participant_id, data in all_results.items():
        pair_1_pref = data.get('pair_1', {}).get('survey', {}).get('q1_preference', 'N/A')
        pair_2_pref = data.get('pair_2', {}).get('survey', {}).get('q1_preference', 'N/A')
        is_consistent = "Yes" if pair_1_pref == pair_2_pref and pair_1_pref != 'N/A' else "No"
        
        consistency_data.append({
            'Participant ID': participant_id,
            'Pair 1 Choice': f"Assistant {pair_1_pref}" if pair_1_pref != 'N/A' else 'N/A',
            'Pair 2 Choice': f"Assistant {pair_2_pref}" if pair_2_pref != 'N/A' else 'N/A',
            'Consistent?': is_consistent
        })
    
    if consistency_data:
        df_consistency = pd.DataFrame(consistency_data)
        st.dataframe(df_consistency, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Across-Subject Consistency
    st.markdown("#### Across-Subject Preference Summary")
    
    # Aggregate counts for each question
    q1_counts = {'A': 0, 'B': 0}
    q3_counts = {'A': 0, 'B': 0}
    q4_counts = {'A': 0, 'B': 0}
    
    for participant_id, data in all_results.items():
        for pair_key in ['pair_1', 'pair_2']:
            survey = data.get(pair_key, {}).get('survey', {})
            
            if survey.get('q1_preference') in ['A', 'B']:
                q1_counts[survey['q1_preference']] += 1
            if survey.get('q3_useful') in ['A', 'B']:
                q3_counts[survey['q3_useful']] += 1
            if survey.get('q4_actionable') in ['A', 'B']:
                q4_counts[survey['q4_actionable']] += 1
    
    total_q1 = q1_counts['A'] + q1_counts['B']
    total_q3 = q3_counts['A'] + q3_counts['B']
    total_q4 = q4_counts['A'] + q4_counts['B']
    
    summary_data = [
        {
            'Metric': 'Q1 (Overall Preference)',
            'Assistant A': f"{q1_counts['A']} ({q1_counts['A']/total_q1*100:.0f}%)" if total_q1 > 0 else "0 (0%)",
            'Assistant B': f"{q1_counts['B']} ({q1_counts['B']/total_q1*100:.0f}%)" if total_q1 > 0 else "0 (0%)"
        },
        {
            'Metric': 'Q3 (Trip Planning Usefulness)',
            'Assistant A': f"{q3_counts['A']} ({q3_counts['A']/total_q3*100:.0f}%)" if total_q3 > 0 else "0 (0%)",
            'Assistant B': f"{q3_counts['B']} ({q3_counts['B']/total_q3*100:.0f}%)" if total_q3 > 0 else "0 (0%)"
        },
        {
            'Metric': 'Q4 (Actionability)',
            'Assistant A': f"{q4_counts['A']} ({q4_counts['A']/total_q4*100:.0f}%)" if total_q4 > 0 else "0 (0%)",
            'Assistant B': f"{q4_counts['B']} ({q4_counts['B']/total_q4*100:.0f}%)" if total_q4 > 0 else "0 (0%)"
        }
    ]
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # 4. Reasons for Preference Breakdown
    st.markdown("### 2. Reasons for Preference Breakdown")
    
    # Define all possible reasons
    all_reasons = [
        "The responses were easy to understand",
        "I could quickly get the information I wanted",
        "The answer was specific and actionable",
        "The assistant felt personalized to my needs",
        "The conversation flow felt more natural",
        "The response was concise without unnecessary details",
        "The assistant reflected what I had already said",
        "It was easy to know what to do next"
    ]
    
    reason_counts = {reason: {'A': 0, 'B': 0} for reason in all_reasons}
    reason_counts['Other'] = {'A': 0, 'B': 0}
    
    for participant_id, data in all_results.items():
        for pair_key in ['pair_1', 'pair_2']:
            survey = data.get(pair_key, {}).get('survey', {})
            preferred = survey.get('q1_preference')
            reasons = survey.get('q2_reasons', [])
            
            if preferred in ['A', 'B']:
                for reason in reasons:
                    if reason.startswith("Other:"):
                        reason_counts['Other'][preferred] += 1
                    elif reason in reason_counts:
                        reason_counts[reason][preferred] += 1
    
    reason_data = []
    for reason, counts in reason_counts.items():
        reason_data.append({
            'Reason': reason if len(reason) < 40 else reason[:37] + "...",
            'When A Preferred': counts['A'],
            'When B Preferred': counts['B']
        })
    
    df_reasons = pd.DataFrame(reason_data)
    st.dataframe(df_reasons, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # 3. Improvement Suggestions Summary
    st.markdown("### 3. Improvement Suggestions Summary")
    
    suggestions_a = []
    suggestions_b = []
    
    for participant_id, data in all_results.items():
        for pair_num, pair_key in enumerate(['pair_1', 'pair_2'], 1):
            survey = data.get(pair_key, {}).get('survey', {})
            
            if survey.get('q5_improvements_A'):
                suggestions_a.append({
                    'source': f"[{participant_id}, Pair {pair_num}]",
                    'text': survey['q5_improvements_A']
                })
            if survey.get('q5_improvements_B'):
                suggestions_b.append({
                    'source': f"[{participant_id}, Pair {pair_num}]",
                    'text': survey['q5_improvements_B']
                })
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Assistant A - All Suggestions")
        if suggestions_a:
            for s in suggestions_a:
                st.markdown(f"**{s['source']}:** {s['text']}")
        else:
            st.caption("_No suggestions recorded_")
    
    with col2:
        st.markdown("#### Assistant B - All Suggestions")
        if suggestions_b:
            for s in suggestions_b:
                st.markdown(f"**{s['source']}:** {s['text']}")
        else:
            st.caption("_No suggestions recorded_")

def show_pilot_detail_view(all_results):
    """Show the detailed view for a specific participant and pair."""
    
    if not all_results:
        st.info("No pilot study results available yet. Complete some pilot sessions first.")
        return
    
    st.markdown("---")
    
    # Navigation & Filtering
    col1, col2 = st.columns(2)
    
    with col1:
        participant_options = list(all_results.keys())
        selected_participant = st.selectbox(
            "Select Participant:",
            options=participant_options,
            key="analysis_participant"
        )
    
    with col2:
        selected_pair = st.selectbox(
            "Select Pair:",
            options=["Pair 1", "Pair 2"],
            key="analysis_pair"
        )
    
    if not selected_participant:
        return
    
    pair_key = 'pair_1' if selected_pair == "Pair 1" else 'pair_2'
    pair_data = all_results.get(selected_participant, {}).get(pair_key, {})
    
    if not pair_data:
        st.warning("No data available for this selection.")
        return
    
    # Get session data
    session_1 = pair_data.get('session_1', {})
    session_2 = pair_data.get('session_2', {})
    survey = pair_data.get('survey', {})
    
    # Header information
    st.markdown("---")
    st.markdown("### Session Information")
    
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.markdown(f"**Participant ID:** {selected_participant}")
        st.markdown(f"**Pair #:** {selected_pair[-1]}")
    with info_col2:
        st.markdown(f"**Session 1:** Query = {session_1.get('query', 'N/A')}, Assistant = {session_1.get('assistant', 'N/A')}")
        st.markdown(f"**Session 2:** Query = {session_2.get('query', 'N/A')}, Assistant = {session_2.get('assistant', 'N/A')}")
    
    st.markdown("---")
    
    # Side-by-Side Conversation View
    st.markdown("### Conversation Comparison")
    
    conv_col1, conv_col2 = st.columns(2)
    
    with conv_col1:
        assistant_1 = session_1.get('assistant', '?')
        query_1 = session_1.get('query', '?')
        st.markdown(f"#### Session 1 — Assistant {assistant_1} — Query: {query_1}")
        
        messages_1 = session_1.get('messages', [])
        if messages_1:
            with st.container(height=350):
                for msg in messages_1:
                    if msg['role'] == 'user':
                        st.markdown(f"""<div style="background-color: #e3f2fd; padding: 8px; border-radius: 8px; margin: 5px 0;">
                            <strong>You:</strong> {msg['content']}
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div style="background-color: #f5f5f5; padding: 8px; border-radius: 8px; margin: 5px 0;">
                            <strong>Assistant:</strong> {msg['content']}
                        </div>""", unsafe_allow_html=True)
        else:
            st.caption("_No conversation recorded_")
        
        if session_1.get('notes'):
            st.markdown("**Notes:**")
            st.info(session_1['notes'])
    
    with conv_col2:
        assistant_2 = session_2.get('assistant', '?')
        query_2 = session_2.get('query', '?')
        st.markdown(f"#### Session 2 — Assistant {assistant_2} — Query: {query_2}")
        
        messages_2 = session_2.get('messages', [])
        if messages_2:
            with st.container(height=350):
                for msg in messages_2:
                    if msg['role'] == 'user':
                        st.markdown(f"""<div style="background-color: #e3f2fd; padding: 8px; border-radius: 8px; margin: 5px 0;">
                            <strong>You:</strong> {msg['content']}
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div style="background-color: #f5f5f5; padding: 8px; border-radius: 8px; margin: 5px 0;">
                            <strong>Assistant:</strong> {msg['content']}
                        </div>""", unsafe_allow_html=True)
        else:
            st.caption("_No conversation recorded_")
        
        if session_2.get('notes'):
            st.markdown("**Notes:**")
            st.info(session_2['notes'])
    
    st.markdown("---")
    
    # Survey Responses for This Pair
    st.markdown("### Survey Responses")
    
    if survey:
        # Q1
        st.markdown(f"**Q1 - Overall Preference:** Assistant {survey.get('q1_preference', 'N/A')}")
        if survey.get('q1_explanation'):
            st.markdown("**Q1 Explanation:**")
            st.info(survey['q1_explanation'])
        
        # Q2
        st.markdown("**Q2 - Reasons for Preference:**")
        reasons = survey.get('q2_reasons', [])
        if reasons:
            for reason in reasons:
                st.markdown(f"- {reason}")
        else:
            st.caption("_No reasons selected_")
        
        # Q3 & Q4
        resp_col1, resp_col2 = st.columns(2)
        with resp_col1:
            st.markdown(f"**Q3 - More Useful for Trip Planning:** Assistant {survey.get('q3_useful', 'N/A')}")
        with resp_col2:
            st.markdown(f"**Q4 - More Actionable:** Assistant {survey.get('q4_actionable', 'N/A')}")
        
        # Q5 Improvement Suggestions
        st.markdown("**Q5 - Improvement Suggestions:**")
        imp_col1, imp_col2 = st.columns(2)
        
        # Map UI labels to actual assistants
        assistant_1_actual = survey.get('assistant_1_actual', '?')
        assistant_2_actual = survey.get('assistant_2_actual', '?')
        
        with imp_col1:
            st.markdown(f"**Suggestions for Assistant {assistant_1_actual}:**")
            if survey.get('q5_improvements_assistant_1_ui'):
                st.info(survey['q5_improvements_assistant_1_ui'])
            else:
                st.caption("_No suggestions_")
        
        with imp_col2:
            st.markdown(f"**Suggestions for Assistant {assistant_2_actual}:**")
            if survey.get('q5_improvements_assistant_2_ui'):
                st.info(survey['q5_improvements_assistant_2_ui'])
            else:
                st.caption("_No suggestions_")
    else:
        st.warning("No survey data recorded for this pair.")

def load_demo_pilot_data():
    """Load demo data for testing the analysis page."""
    demo_data = {
        "P1": {
            "pair_1": {
                "survey": {
                    "q1_preference": "A",
                    "q1_explanation": "Assistant A provided more detailed and actionable suggestions.",
                    "q2_reasons": ["The answer was specific and actionable", "The conversation flow felt more natural"],
                    "q3_useful": "A",
                    "q4_actionable": "A",
                    "q5_improvements_A": "Could include more budget information.",
                    "q5_improvements_B": "Responses were too brief.",
                    "assistant_1_actual": "A",
                    "assistant_2_actual": "B"
                },
                "session_1": {
                    "messages": [
                        {"role": "user", "content": "I'm planning a 3-day trip to Tokyo."},
                        {"role": "assistant", "content": "Great choice! For a 3-day Tokyo trip, I recommend: Day 1: Explore Shibuya and Harajuku. Day 2: Visit Senso-ji Temple and Akihabara. Day 3: Day trip to Mt. Fuji or explore Shinjuku."}
                    ],
                    "notes": "Good suggestions but could be more detailed.",
                    "assistant": "A",
                    "query": "Q1"
                },
                "session_2": {
                    "messages": [
                        {"role": "user", "content": "I want to visit Paris for a weekend."},
                        {"role": "assistant", "content": "Paris is lovely! Visit the Eiffel Tower, Louvre, and Notre-Dame."}
                    ],
                    "notes": "Too brief.",
                    "assistant": "B",
                    "query": "Q2"
                }
            },
            "pair_2": {
                "survey": {
                    "q1_preference": "B",
                    "q1_explanation": "This time B was more helpful with practical tips.",
                    "q2_reasons": ["I could quickly get the information I wanted", "The response was concise without unnecessary details"],
                    "q3_useful": "B",
                    "q4_actionable": "A",
                    "q5_improvements_A": "Too much information at once.",
                    "q5_improvements_B": "Perfect balance of detail.",
                    "assistant_1_actual": "B",
                    "assistant_2_actual": "A"
                },
                "session_1": {
                    "messages": [
                        {"role": "user", "content": "I'm thinking about a week-long trip to Italy."},
                        {"role": "assistant", "content": "Italy is wonderful! Consider Rome (2 days), Florence (2 days), and Venice (2 days)."}
                    ],
                    "notes": "Good overview.",
                    "assistant": "B",
                    "query": "Q3"
                },
                "session_2": {
                    "messages": [
                        {"role": "user", "content": "I'd like to explore Seoul for 4 days."},
                        {"role": "assistant", "content": "Seoul offers rich culture! Day 1: Gyeongbokgung Palace. Day 2: Myeongdong shopping. Day 3: Bukchon Hanok Village. Day 4: DMZ tour or N Seoul Tower."}
                    ],
                    "notes": "Very detailed itinerary.",
                    "assistant": "A",
                    "query": "Q4"
                }
            }
        },
        "P2": {
            "pair_1": {
                "survey": {
                    "q1_preference": "B",
                    "q1_explanation": "Preferred the concise responses.",
                    "q2_reasons": ["The responses were easy to understand", "The response was concise without unnecessary details"],
                    "q3_useful": "B",
                    "q4_actionable": "B",
                    "q5_improvements_A": "Could be more concise.",
                    "q5_improvements_B": "",
                    "assistant_1_actual": "B",
                    "assistant_2_actual": "A"
                },
                "session_1": {
                    "messages": [
                        {"role": "user", "content": "I'm planning a 3-day trip to Tokyo."},
                        {"role": "assistant", "content": "Tokyo 3-day plan: Shibuya, Senso-ji, Akihabara. Enjoy!"}
                    ],
                    "notes": "Brief but useful.",
                    "assistant": "B",
                    "query": "Q1"
                },
                "session_2": {
                    "messages": [
                        {"role": "user", "content": "I want to visit Paris for a weekend."},
                        {"role": "assistant", "content": "Paris weekend: Start with the Eiffel Tower for sunrise views..."}
                    ],
                    "notes": "Very detailed.",
                    "assistant": "A",
                    "query": "Q2"
                }
            },
            "pair_2": {
                "survey": {
                    "q1_preference": "A",
                    "q1_explanation": "More personalized recommendations.",
                    "q2_reasons": ["The assistant felt personalized to my needs", "It was easy to know what to do next"],
                    "q3_useful": "A",
                    "q4_actionable": "A",
                    "q5_improvements_A": "",
                    "q5_improvements_B": "Could ask more questions about preferences.",
                    "assistant_1_actual": "A",
                    "assistant_2_actual": "B"
                },
                "session_1": {
                    "messages": [
                        {"role": "user", "content": "I'm thinking about a week-long trip to Italy."},
                        {"role": "assistant", "content": "What are your interests? Food, art, or history?"}
                    ],
                    "notes": "Good question to start.",
                    "assistant": "A",
                    "query": "Q3"
                },
                "session_2": {
                    "messages": [
                        {"role": "user", "content": "I'd like to explore Seoul for 4 days."},
                        {"role": "assistant", "content": "Seoul is great. Visit palaces and markets."}
                    ],
                    "notes": "Too generic.",
                    "assistant": "B",
                    "query": "Q4"
                }
            }
        }
    }
    
    st.session_state.pilot_all_results = demo_data
    st.success("Demo data loaded successfully!")

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
    st.session_state.session_order = None  # Reset randomized order
    st.session_state.session_1_messages = []  # Reset stored conversation histories
    st.session_state.session_2_messages = []
    st.session_state.session_1_notes = ""  # Reset stored notes
    st.session_state.session_2_notes = ""

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
    elif page == 'pilot':
        show_pilot_page()
    elif page == 'pilot_analysis':
        show_pilot_analysis_page()
    elif page == 'summary':
        show_summary_page()

if __name__ == "__main__":
    main()
