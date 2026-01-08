"""Deal Intelligence Platform - Streamlit Dashboard."""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from dashboard.config import setup_page
from dashboard.pages import documents, home

# Page configuration
setup_page()

# Sidebar navigation
st.sidebar.title("🎯 Deal Intelligence")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "📄 Documents", "📊 Briefings", "🎙️ Calls"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="font-size: 0.8em; color: #666;">
    <strong>Status</strong><br>
    ✅ Documents: Active<br>
    🔜 Briefings: Coming<br>
    ⏳ Calls: Planned
    </div>
    """,
    unsafe_allow_html=True,
)

# Route to pages
if page == "🏠 Home":
    home.render()
elif page == "📄 Documents":
    documents.render()
elif page == "📊 Briefings":
    st.title("📊 Deal Briefings")
    st.info("Multi-agent briefing generation coming in M4!")
    st.markdown(
        """
        This feature will include:
        - 🤖 Orchestrator agent coordination
        - 🏢 Company research
        - 📈 Similar deals analysis
        - ⚔️ Competitive positioning
        - 💡 Proposal recommendations
        """
    )
elif page == "🎙️ Calls":
    st.title("🎙️ Call Analysis")
    st.info("Voice analysis coming in M5-M8!")
    st.markdown(
        """
        This feature will include:
        - 🎤 Audio transcription (Whisper)
        - 😊 Sentiment analysis
        - 👤 Named entity recognition
        - 🏷️ Topic classification
        - 📊 Visual analytics
        """
    )
