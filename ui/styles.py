"""
Streamlit UI styles module.
"""

from utils.constants import (
    THEME_PRIMARY,
    THEME_SUCCESS,
    THEME_WARNING,
    THEME_ERROR,
    THEME_DARK_BG,
    THEME_LIGHT_BG
)


def get_custom_css() -> str:
    """Get the custom CSS for Streamlit UI."""
    return f"""
    <style>
    /* Main container styling */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* Header styling */
    .header-container {{
        background: linear-gradient(90deg, #1e3a8a 0%, {THEME_PRIMARY} 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    .header-title {{
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }}
    
    .header-subtitle {{
        font-size: 1rem;
        opacity: 0.9;
        margin-bottom: 0;
    }}
    
    /* Card styling */
    .metric-card {{
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid {THEME_PRIMARY};
        margin-bottom: 1rem;
    }}
    
    .upload-card {{
        background: {THEME_LIGHT_BG};
        border: 2px dashed #cbd5e1;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }}
    
    .upload-card:hover {{
        border-color: {THEME_PRIMARY};
        background: #eff6ff;
    }}
    
    /* Status badges */
    .status-success {{
        background: #dcfce7;
        color: #{THEME_SUCCESS.lstrip('#')};
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }}
    
    .status-warning {{
        background: #fef3c7;
        color: #{THEME_WARNING.lstrip('#')};
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }}
    
    .status-error {{
        background: #fee2e2;
        color: {THEME_ERROR};
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }}
    
    /* Quality score styling */
    .quality-metric {{
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    
    .quality-score {{
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }}
    
    .quality-label {{
        font-size: 0.9rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Transcript styling */
    .transcript-container {{
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.5rem;
        font-family: 'Courier New', monospace;
        line-height: 1.6;
        max-height: 400px;
        overflow-y: auto;
    }}
    
    .speaker-label {{
        font-weight: 700;
        color: #1e40af;
        margin-right: 0.5rem;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(90deg, {THEME_PRIMARY} 0%, #1e40af 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        transform: translateY(-1px);
    }}
    
    /* Sidebar styling */
    .sidebar .sidebar-content {{
        background: {THEME_LIGHT_BG};
    }}
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {THEME_PRIMARY} 0%, #1e40af 100%);
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {THEME_DARK_BG};
        padding: 8px;
        border-radius: 10px;
        margin-bottom: 20px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        padding: 0 20px;
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(90deg, {THEME_PRIMARY} 0%, #1e40af 100%);
        color: white;
        border: 1px solid {THEME_PRIMARY};
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: #334155;
        color: #e2e8f0;
    }}
    
    .stTabs [aria-selected="true"]:hover {{
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
    }}
    </style>
    """


def inject_custom_css():
    """Inject custom CSS into Streamlit app."""
    import streamlit as st
    st.markdown(get_custom_css(), unsafe_allow_html=True)


def render_header():
    """Render the professional header section."""
    import streamlit as st
    st.markdown("""
    <div class="header-container">
        <div class="header-title"><i class="fas fa-headset"></i> AI Call Center Assistant</div>
        <div class="header-subtitle">Enterprise-grade call analysis with automated summarization and quality scoring</div>
    </div>
    """, unsafe_allow_html=True)