"""Home page for the dashboard."""

import requests
import streamlit as st

from dashboard.config import API_URL


def render():
    """Render the home page."""
    st.title("🎯 Deal Intelligence Platform")
    st.markdown(
        """
        > Accelerate deal preparation from hours to minutes with AI-powered 
        > knowledge retrieval and multi-agent analysis.
        """
    )

    st.markdown("---")

    # Status cards
    col1, col2, col3, col4 = st.columns(4)

    # Fetch status from API
    try:
        response = requests.get(f"{API_URL}/status", timeout=5)
        if response.ok:
            data = response.json()
            doc_count = data.get("vector_store", {}).get("document_count", 0)
            model = data.get("config", {}).get("model", "unknown")
        else:
            doc_count = "N/A"
            model = "N/A"
    except requests.exceptions.RequestException:
        doc_count = "⚠️"
        model = "⚠️"
        st.warning(
            "⚠️ API not reachable. Start the server with `make dev` in another terminal."
        )

    with col1:
        st.metric("📄 Documents", doc_count)

    with col2:
        st.metric("🤖 Agents", "5")

    with col3:
        st.metric("🧠 Model", model)

    with col4:
        features = "3"
        st.metric("✨ Features", features)

    st.markdown("---")

    # Feature overview
    st.subheader("Platform Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            ### 📄 Documents
            **Status: ✅ Active**
            
            - Ingest knowledge base documents
            - Semantic search with filters
            - Query rewriting via LLM
            - Source tracking & citations
            """
        )

    with col2:
        st.markdown(
            """
            ### 📊 Briefings
            **Status: ✅ Active**
            
            - Multi-agent orchestration
            - Company research
            - Similar deals analysis
            - Competitive positioning
            """
        )

    with col3:
        st.markdown(
            """
            ### 🎙️ Calls
            **Status: ⏳ Planned (M5-M8)**
            
            - Audio transcription
            - Sentiment analysis
            - Named entity recognition
            - Topic classification
            """
        )

    st.markdown("---")

    # Quick actions
    st.subheader("Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Ingest Documents", use_container_width=True):
            with st.spinner("Ingesting documents..."):
                try:
                    response = requests.post(f"{API_URL}/documents/ingest", timeout=60)
                    if response.ok:
                        data = response.json()
                        st.success(
                            f"✅ Ingested {data.get('chunks_ingested', 0)} chunks!"
                        )
                    else:
                        st.error(f"Failed: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"API Error: {e}")

    with col2:
        if st.button("🔍 Go to Search", use_container_width=True):
            st.info("Navigate to Documents page using the sidebar →")
