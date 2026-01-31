"""Briefings page - Generate deal intelligence briefings."""

import requests
import streamlit as st

from dashboard.config import API_URL

# Industry options
INDUSTRIES = [
    "healthcare",
    "fintech",
    "manufacturing",
    "technology",
    "retail",
    "education",
    "other",
]

# Company size options
COMPANY_SIZES = [
    ("startup", "Startup (< 50 employees)"),
    ("mid-market", "Mid-Market (50-500 employees)"),
    ("enterprise", "Enterprise (500+ employees)"),
]

# Meeting types
MEETING_TYPES = [
    ("initial_call", "Initial Discovery Call"),
    ("demo", "Product Demo"),
    ("negotiation", "Negotiation/Pricing"),
    ("executive", "Executive Presentation"),
    ("technical", "Technical Deep-Dive"),
]


def render():
    """Render the briefings page."""
    st.title("📊 Deal Briefings")
    st.markdown(
        """
        > Generate AI-powered deal intelligence with multi-agent orchestration.
        > Our specialists research, analyze, and synthesize insights from your knowledge base.
        """
    )

    st.markdown("---")

    # Two column layout: form and results
    col_form, col_results = st.columns([1, 2])

    with col_form:
        st.subheader("🎯 Deal Context")

        with st.form("briefing_form"):
            # Company name (required)
            company_name = st.text_input(
                "Company Name *",
                placeholder="e.g., Acme Healthcare Inc.",
                help="The target company for this deal",
            )

            # Industry
            industry = st.selectbox(
                "Industry",
                options=INDUSTRIES,
                index=0,
                help="Industry vertical of the target company",
            )

            # Company size
            company_size = st.selectbox(
                "Company Size",
                options=[size[0] for size in COMPANY_SIZES],
                format_func=lambda x: next(s[1] for s in COMPANY_SIZES if s[0] == x),
                index=1,
                help="Approximate size of the target company",
            )

            # Meeting type
            meeting_type = st.selectbox(
                "Meeting Type",
                options=[m[0] for m in MEETING_TYPES],
                format_func=lambda x: next(m[1] for m in MEETING_TYPES if m[0] == x),
                index=0,
                help="Type of upcoming meeting or call",
            )

            # Specific questions
            specific_questions = st.text_area(
                "Specific Questions (optional)",
                placeholder="One question per line...\nHow do we compare to Competitor X?\nWhat pricing should we offer?",
                help="Any specific questions you want addressed",
            )

            # Submit button
            submitted = st.form_submit_button(
                "🚀 Generate Briefing",
                use_container_width=True,
            )

    with col_results:
        st.subheader("📋 Briefing Results")

        if submitted:
            if not company_name:
                st.error("Please enter a company name.")
            else:
                # Parse specific questions
                questions = [
                    q.strip() for q in specific_questions.split("\n") if q.strip()
                ]

                # Prepare request
                request_data = {
                    "company_name": company_name,
                    "industry": industry,
                    "company_size": company_size,
                    "meeting_type": meeting_type,
                    "specific_questions": questions,
                }

                # Show loading state with agent progress
                with st.spinner("🤖 Orchestrating agents..."):
                    progress_placeholder = st.empty()

                    # Show agent progress
                    agents = [
                        "🏢 Company Researcher",
                        "📈 Similar Deals Finder",
                        "⚔️ Competitor Analyst",
                        "💡 Proposal Drafter",
                    ]

                    progress_bar = st.progress(0)

                    for i, agent in enumerate(agents):
                        progress_placeholder.info(f"Running {agent}...")
                        progress_bar.progress((i + 1) * 25)

                    try:
                        response = requests.post(
                            f"{API_URL}/briefings",
                            json=request_data,
                            timeout=120,
                        )

                        progress_bar.empty()
                        progress_placeholder.empty()

                        if response.ok:
                            briefing = response.json()
                            render_briefing(briefing, company_name)
                        else:
                            st.error(f"Failed to generate briefing: {response.text}")

                    except requests.exceptions.Timeout:
                        st.error(
                            "Request timed out. The briefing generation is taking too long."
                        )
                    except requests.exceptions.RequestException as e:
                        st.error(f"API Error: {e}")
                        st.info("Make sure the API server is running: `make dev`")
        else:
            # Show placeholder
            st.info(
                "👈 Fill out the deal context form and click **Generate Briefing** to get started."
            )

            # Show example output
            with st.expander("📖 Example Briefing Output"):
                st.markdown(
                    """
                    A briefing includes:
                    
                    **Company Summary**
                    - Industry overview and context
                    - Key priorities and trends
                    - Important considerations
                    
                    **Similar Deals**
                    - Past deals with similar characteristics
                    - Success factors and learnings
                    - Common objections encountered
                    
                    **Competitive Positioning**
                    - Key differentiators
                    - Objection responses
                    - Positioning strategy
                    
                    **Recommended Approach**
                    - Talking points for the meeting
                    - Discovery questions to ask
                    - Pricing guidance
                    """
                )


def render_briefing(briefing: dict, company_name: str):
    """Render a complete briefing."""
    metadata = briefing.get("metadata", {})

    # Success header
    st.success(
        f"✅ Briefing generated for **{company_name}** using "
        f"{len(metadata.get('agents_used', []))} agents"
    )

    # Metadata bar
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 Sources Cited", metadata.get("documents_cited", 0))
    with col2:
        st.metric("🎯 Confidence", f"{metadata.get('confidence_score', 0) * 100:.0f}%")
    with col3:
        agents = metadata.get("agents_used", [])
        st.metric("🤖 Agents Used", len(agents))

    st.markdown("---")

    # Company Summary
    company_summary = briefing.get("company_summary", {})
    if company_summary:
        st.subheader("🏢 Company & Industry Context")

        overview = company_summary.get("overview", "")
        if overview:
            st.markdown(f"_{overview}_")

        # Industry context
        industry_ctx = company_summary.get("industry_context", {})
        if industry_ctx:
            col1, col2 = st.columns(2)
            with col1:
                priorities = industry_ctx.get("priorities", [])
                if priorities:
                    st.markdown("**Key Priorities:**")
                    for p in priorities:
                        st.markdown(f"- {p}")

            with col2:
                trends = industry_ctx.get("trends", [])
                if trends:
                    st.markdown("**Market Trends:**")
                    for t in trends:
                        st.markdown(f"- {t}")

        # Considerations
        considerations = company_summary.get("considerations", [])
        if considerations:
            st.markdown("**Considerations:**")
            for c in considerations:
                st.markdown(f"- ⚠️ {c}")

        # Sources
        sources = company_summary.get("sources", [])
        if sources:
            with st.expander("📚 Sources"):
                for s in sources:
                    st.markdown(f"- `{s}`")

    st.markdown("---")

    # Similar Deals
    similar_deals = briefing.get("similar_deals", [])
    if similar_deals:
        st.subheader("📈 Similar Deals")

        for deal in similar_deals:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{deal.get('company', 'Unknown')}**")
                with col2:
                    outcome = deal.get("outcome", "unknown")
                    emoji = (
                        "✅"
                        if outcome == "won"
                        else "❌"
                        if outcome == "lost"
                        else "⏳"
                    )
                    st.markdown(f"{emoji} {outcome.upper()}")
                with col3:
                    value = deal.get("deal_value")
                    if value:
                        st.markdown(f"💰 ${value:,}")

                learnings = deal.get("key_learnings", "")
                if learnings:
                    st.markdown(f"_💡 {learnings}_")

                st.markdown("---")

    # Competitive Positioning
    competitive = briefing.get("competitive_positioning")
    if competitive:
        st.subheader("⚔️ Competitive Positioning")

        summary = competitive.get("summary", "")
        if summary:
            st.info(summary)

        objections = competitive.get("objection_responses", [])
        if objections:
            st.markdown("**Objection Responses:**")
            for obj in objections:
                st.markdown(f"- 💬 {obj}")

        sources = competitive.get("sources", [])
        if sources:
            with st.expander("📚 Sources"):
                for s in sources:
                    st.markdown(f"- `{s}`")

    st.markdown("---")

    # Recommended Approach
    approach = briefing.get("recommended_approach")
    if approach:
        st.subheader("💡 Recommended Approach")

        col1, col2 = st.columns(2)

        with col1:
            talking_points = approach.get("talking_points", [])
            if talking_points:
                st.markdown("**Talking Points:**")
                for i, point in enumerate(talking_points, 1):
                    st.markdown(f"{i}. {point}")

        with col2:
            questions = approach.get("questions_to_ask", [])
            if questions:
                st.markdown("**Questions to Ask:**")
                for q in questions:
                    st.markdown(f"- ❓ {q}")

        # Pricing guidance
        pricing = approach.get("pricing_guidance")
        if pricing:
            st.success(f"💰 **Pricing Guidance:** {pricing}")

        sources = approach.get("sources", [])
        if sources:
            with st.expander("📚 Sources"):
                for s in sources:
                    st.markdown(f"- `{s}`")

    st.markdown("---")

    # Export options
    st.subheader("📤 Export")
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "📄 Download JSON",
            data=str(briefing),
            file_name=f"briefing_{company_name.lower().replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        st.button(
            "📋 Copy to Clipboard",
            disabled=True,
            use_container_width=True,
            help="Coming soon!",
        )
