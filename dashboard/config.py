"""Dashboard configuration and styling."""

import streamlit as st

# Custom CSS
CUSTOM_CSS = """
<style>
/* Main container */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Headers */
h1 {
    color: #1f2937;
    font-weight: 700;
}

/* Cards */
.stMetric {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 0.75rem;
    color: white;
}

.stMetric label {
    color: rgba(255,255,255,0.8) !important;
}

.stMetric [data-testid="stMetricValue"] {
    color: white !important;
}

/* Search result cards */
.search-result {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.search-result:hover {
    border-color: #667eea;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

/* Score badge */
.score-badge {
    display: inline-block;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 600;
}

/* Document type badge */
.doc-type-badge {
    display: inline-block;
    background: #e0e7ff;
    color: #4338ca;
    padding: 0.25rem 0.75rem;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
}

section[data-testid="stSidebar"] .stMarkdown {
    color: white;
}

section[data-testid="stSidebar"] .stRadio label {
    color: white !important;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 0.5rem;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    transition: transform 0.2s, box-shadow 0.2s;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Info box */
.stAlert {
    border-radius: 0.5rem;
}

/* Expander */
.streamlit-expanderHeader {
    font-weight: 600;
    color: #1f2937;
}
</style>
"""


def setup_page():
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="Deal Intelligence Platform",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# API base URL
API_URL = "http://localhost:8000"
