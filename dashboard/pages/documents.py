"""Documents page for the dashboard."""

import requests
import streamlit as st

# API base URL
API_URL = "http://localhost:8000"


def render():
    """Render the documents page."""
    st.title("📄 Document Search")
    st.markdown("Search your knowledge base using semantic similarity.")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["🔍 Search", "📋 Browse", "📥 Ingest"])

    with tab1:
        render_search()

    with tab2:
        render_browse()

    with tab3:
        render_ingest()


def render_search():
    """Render the search interface."""
    # Search input
    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Search query",
            placeholder="e.g., healthcare deals, competitor analysis, pricing...",
            label_visibility="collapsed",
        )

    with col2:
        top_k = st.selectbox("Results", [3, 5, 10], index=1, label_visibility="collapsed")

    # Advanced filters
    with st.expander("🎛️ Advanced Filters"):
        col1, col2, col3 = st.columns(3)

        with col1:
            doc_type = st.selectbox(
                "Document Type",
                ["All", "deal", "proposal", "competitor", "product", "industry"],
            )

        with col2:
            industry = st.selectbox(
                "Industry",
                ["All", "healthcare", "fintech", "manufacturing"],
            )

        with col3:
            outcome = st.selectbox(
                "Deal Outcome",
                ["All", "won", "lost", "pending"],
            )

    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True) and query:
        # Build filters
        filters = {}
        if doc_type != "All":
            filters["doc_type"] = doc_type
        if industry != "All":
            filters["industry"] = industry
        if outcome != "All":
            filters["outcome"] = outcome

        # Execute search
        with st.spinner("Searching..."):
            try:
                payload = {
                    "query": query,
                    "top_k": top_k,
                }
                if filters:
                    payload["filters"] = filters

                response = requests.post(
                    f"{API_URL}/documents/search",
                    json=payload,
                    timeout=30,
                )

                if response.ok:
                    data = response.json()
                    results = data.get("results", [])
                    total = data.get("total_searched", 0)

                    st.markdown(f"**Found {len(results)} results** (searched {total} chunks)")
                    st.markdown("---")

                    if not results:
                        st.info(
                            "No results found. Try broadening your search or ingesting documents first."
                        )
                    else:
                        render_search_results(results)
                else:
                    error = response.json().get("detail", response.text)
                    st.error(f"Search failed: {error}")

            except requests.exceptions.RequestException as e:
                st.error(f"API Error: {e}")

    elif not query and st.session_state.get("search_clicked"):
        st.warning("Please enter a search query.")


def render_search_results(results: list):
    """Render search results with nice formatting."""
    for i, result in enumerate(results, 1):
        score = result.get("score", 0)
        content = result.get("content", "")
        metadata = result.get("metadata", {})

        doc_type = metadata.get("doc_type", "unknown")
        source_file = metadata.get("source_file", "unknown")
        doc_id = metadata.get("doc_id", "unknown")

        # Score color
        if score >= 0.8:
            score_color = "#10b981"  # green
        elif score >= 0.6:
            score_color = "#f59e0b"  # amber
        else:
            score_color = "#ef4444"  # red

        # Result card
        st.markdown(
            f"""
            <div class="search-result">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div>
                        <span class="doc-type-badge">{doc_type}</span>
                        <span style="margin-left: 0.5rem; color: #6b7280; font-size: 0.875rem;">
                            {source_file}
                        </span>
                    </div>
                    <span style="background: {score_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600;">
                        {score:.0%}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Content in expander
        with st.expander(f"📄 {doc_id}", expanded=(i == 1)):
            st.markdown(content)

            # Metadata
            st.markdown("---")
            cols = st.columns(4)
            with cols[0]:
                st.caption(f"**Type:** {doc_type}")
            with cols[1]:
                st.caption(f"**Industry:** {metadata.get('industry', 'N/A')}")
            with cols[2]:
                st.caption(f"**Outcome:** {metadata.get('outcome', 'N/A')}")
            with cols[3]:
                st.caption(f"**Chunk:** {metadata.get('chunk_index', 0)}")


def render_browse():
    """Render the document browser."""
    st.markdown("### Indexed Documents")

    if st.button("🔄 Refresh", key="refresh_browse"):
        st.rerun()

    try:
        response = requests.get(f"{API_URL}/documents", timeout=10)

        if response.ok:
            data = response.json()
            documents = data.get("documents", [])
            total_chunks = data.get("total_chunks", 0)

            if not documents:
                st.info(
                    "No documents indexed yet. Go to the **Ingest** tab to add documents."
                )
            else:
                st.markdown(
                    f"**{len(documents)} documents** indexed ({total_chunks} total chunks)"
                )
                st.markdown("---")

                # Group by doc_type
                by_type = {}
                for doc in documents:
                    dtype = doc.get("doc_type", "other")
                    if dtype not in by_type:
                        by_type[dtype] = []
                    by_type[dtype].append(doc)

                # Display by type
                for doc_type, docs in sorted(by_type.items()):
                    with st.expander(f"📁 {doc_type.upper()} ({len(docs)})", expanded=True):
                        for doc in docs:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{doc.get('doc_id')}**")
                                st.caption(doc.get("source_file", ""))
                            with col2:
                                industry = doc.get("industry")
                                if industry:
                                    st.caption(f"🏢 {industry}")
        else:
            st.error(f"Failed to fetch documents: {response.text}")

    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")


def render_ingest():
    """Render the ingestion interface."""
    st.markdown("### Ingest Documents")

    st.markdown(
        """
        Ingest documents from the `knowledge_base/` directory into the vector store.
        
        **Supported document types:**
        - 📁 `deals/` — Past deal records
        - 📁 `proposals/` — Proposal templates
        - 📁 `competitors/` — Competitor analyses
        - 📁 `products/` — Product documentation
        - 📁 `industries/` — Industry playbooks
        - 📁 `case_studies/` — Case studies
        """
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Run Ingestion", type="primary", use_container_width=True):
            with st.spinner("Ingesting documents... This may take a minute."):
                try:
                    response = requests.post(
                        f"{API_URL}/documents/ingest", timeout=120
                    )

                    if response.ok:
                        data = response.json()
                        chunks = data.get("chunks_ingested", 0)
                        st.success(f"✅ Successfully ingested **{chunks}** chunks!")
                        st.balloons()
                    else:
                        error = response.json().get("detail", response.text)
                        st.error(f"Ingestion failed: {error}")

                except requests.exceptions.RequestException as e:
                    st.error(f"API Error: {e}")

    with col2:
        st.info(
            "💡 **Tip:** The ingestion process will clear the existing index and re-ingest all documents."
        )
