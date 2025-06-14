"""Main dashboard application using Streamlit."""

import streamlit as st
from streamlit_option_menu import option_menu

from .pages import (
    chat,
    data_explorer,
    insights,
    ontology_viewer,
    settings
)


def initialize_session_state():
    """Initialize session state variables."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "current_object" not in st.session_state:
        st.session_state.current_object = None
    
    if "selected_relationship" not in st.session_state:
        st.session_state.selected_relationship = None


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Palantir AIP Dashboard",
        page_icon="🔮",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            background-color: #f5f5f5;
        }
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stSidebar {
            background-color: #ffffff;
            padding: 2rem 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.image("assets/logo.png", width=200)
        st.markdown("## Palantir AIP")
        
        selected = option_menu(
            menu_title=None,
            options=[
                "Chat Assistant",
                "Data Explorer",
                "Ontology Viewer",
                "Insights",
                "Settings"
            ],
            icons=[
                "chat-dots",
                "search",
                "diagram-3",
                "graph-up",
                "gear"
            ],
            default_index=0
        )
    
    # Main content
    if selected == "Chat Assistant":
        chat.render_page()
    
    elif selected == "Data Explorer":
        data_explorer.render_page()
    
    elif selected == "Ontology Viewer":
        ontology_viewer.render_page()
    
    elif selected == "Insights":
        insights.render_page()
    
    elif selected == "Settings":
        settings.render_page()


if __name__ == "__main__":
    main() 