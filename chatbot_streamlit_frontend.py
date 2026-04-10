import streamlit as st
# from chatbot_backend import chatbot
from database_chatbot_backend import chatbot, retrieve_all_threads
from langchain.messages import HumanMessage
import uuid

# ---------- Utility Functions ----------
def generate_thread_id():
    return f"T-{uuid.uuid4()}"

def reset_chat():
    new_id = generate_thread_id()
    st.session_state['thread_id'] = new_id
    add_thread(new_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def get_message_history(thread_id):
    config = {'configurable': {'thread_id': thread_id}}
    return chatbot.get_state(config=config).values['messages']

# ---------- Session State ----------
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

# Ensure thread is stored once
add_thread(st.session_state['thread_id'])

# CONFIG per thread
CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

# ---------- Sidebar ----------
st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat", key="new_chat_btn"):
    reset_chat()

st.sidebar.header("My Conversations")

for i, thread_id in enumerate(st.session_state['chat_threads'][::-1]):
    if st.sidebar.button(thread_id, key=f"thread_btn_{i}"):
        st.session_state['thread_id'] = thread_id
        CONFIG['configurable']['thread_id'] = thread_id

        messages = get_message_history(thread_id)

        temp_msg = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_msg.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_msg

# ---------- Chat UI ----------
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# ---------- Input ----------
user_input = st.chat_input("Type your message here...")

if user_input:
    # Show user message
    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })

    with st.chat_message('user'):
        st.text(user_input)

    # Stream AI response
    with st.chat_message('assistant'):
        stream_generator = (
            chunk.content
            for chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

        ai_reply = st.write_stream(stream_generator)

    # Save AI message
    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_reply
    })