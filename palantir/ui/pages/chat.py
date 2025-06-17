"""Chat assistant page component."""

import datetime
import json
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st
from ..i18n import translate as _

try:
    st.page("chat", _("chat_title"), icon="💬")
except Exception:
    pass

from ...models.llm import ChatMessage, OntologyAssistant

# Initialize the assistant
assistant = OntologyAssistant()

# Chat history directory
CHAT_HISTORY_DIR = Path("chat_history")
CHAT_HISTORY_DIR.mkdir(exist_ok=True)


def save_chat_history(name: str = None):
    """Save current chat history to file.

    Args:
        name: Optional name for the chat history file.
    """
    if not name:
        name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    history = [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        for msg in st.session_state.chat_messages
    ]

    file_path = CHAT_HISTORY_DIR / f"{name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return file_path


def load_chat_history(file_path: Path) -> List[ChatMessage]:
    """Load chat history from file.

    Args:
        file_path: Path to the chat history file.

    Returns:
        List of ChatMessage objects.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        history = json.load(f)

    return [ChatMessage(role=msg["role"], content=msg["content"]) for msg in history]


def format_message(msg: ChatMessage) -> Tuple[str, bool]:
    """Format a chat message for display.

    Args:
        msg: The chat message to format.

    Returns:
        Tuple of (message text, is_user)
    """
    return msg.content, msg.role == "user"


def display_chat_history():
    """Display the chat history."""
    for msg in st.session_state.chat_messages:
        content, is_user = format_message(msg)

        if is_user:
            st.chat_message("user").write(content)
        else:
            st.chat_message("assistant").write(content)


def process_input(user_input: str):
    """Process user input and generate response.

    Args:
        user_input: The user's input message.
    """
    if not user_input:
        return

    # Add user message to history
    user_msg = ChatMessage(role="user", content=user_input)
    st.session_state.chat_messages.append(user_msg)

    # Get assistant response
    response = assistant.process_message(user_input)

    # Add assistant message to history
    assistant_msg = ChatMessage(role="assistant", content=response)
    st.session_state.chat_messages.append(assistant_msg)


def render_page():
    """Render the chat assistant page."""
    st.title("💬 " + _("chat_title"))

    st.markdown(
        """
        Ask questions about your data, explore relationships, or get insights.
        The AI assistant will help you navigate the ontology system.
    """
    )

    # Chat interface
    st.divider()

    # Display chat history
    display_chat_history()

    # Chat input
    user_input = st.chat_input("Type your message here...")

    if user_input:
        process_input(user_input)
        st.rerun()  # Refresh to show new messages

    # Sidebar controls
    with st.sidebar:
        st.markdown("### Chat Controls")

        # Save/Load controls
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Save Chat"):
                chat_name = st.text_input("Chat name (optional):")
                if st.button("Confirm Save"):
                    file_path = save_chat_history(chat_name)
                    st.success(f"Saved to {file_path}")

        with col2:
            if st.button("Load Chat"):
                files = list(CHAT_HISTORY_DIR.glob("*.json"))
                if files:
                    selected = st.selectbox(
                        "Select chat history:",
                        options=files,
                        format_func=lambda x: x.stem,
                    )
                    if st.button("Confirm Load"):
                        st.session_state.chat_messages = load_chat_history(selected)
                        st.rerun()
                else:
                    st.info("No saved chats found")

        if st.button("Clear Chat History"):
            st.session_state.chat_messages = []
            assistant.clear_memory()
            st.rerun()

        # Export options
        st.markdown("### Export Options")
        if st.button("Export as Text"):
            chat_text = "\n\n".join(
                [
                    f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                    for msg in st.session_state.chat_messages
                ]
            )
            st.download_button(
                "Download Chat",
                chat_text,
                file_name=f"chat_export_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt",
                mime="text/plain",
            )

        st.markdown("### Example Questions")
        examples = [
            "Show me all customers who made purchases over $1000",
            "What are the top-selling products this month?",
            "Find orders with delayed shipping",
            "Analyze the relationship between customer age and purchase frequency",
        ]

        for example in examples:
            if st.button(example):
                process_input(example)
                st.rerun()
