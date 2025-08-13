"""
Modern Streamlit UI for AI Call Center Assistant.
"""

import os
import streamlit as st
from dotenv import load_dotenv
import plotly.graph_objects as go

from utils.validation import CallInput, InputType
from workflow import CallCenterWorkflow

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Call Center Assistant",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def inject_custom_css():
    """Inject custom CSS for professional styling."""
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .header-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    
    .header-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin-bottom: 0;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    
    .upload-card {
        background: #f8fafc;
        border: 2px dashed #cbd5e1;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .upload-card:hover {
        border-color: #3b82f6;
        background: #eff6ff;
    }
    
    /* Status badges */
    .status-success {
        background: #dcfce7;
        color: #166534;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .status-warning {
        background: #fef3c7;
        color: #92400e;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .status-error {
        background: #fee2e2;
        color: #dc2626;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    /* Quality score styling */
    .quality-metric {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .quality-score {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .quality-label {
        font-size: 0.9rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Transcript styling */
    .transcript-container {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.5rem;
        font-family: 'Courier New', monospace;
        line-height: 1.6;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .speaker-label {
        font-weight: 700;
        color: #1e40af;
        margin-right: 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        transform: translateY(-1px);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #f8fafc;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1e293b;
        padding: 8px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        padding: 0 20px;
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
        color: white;
        border: 1px solid #3b82f6;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #334155;
        color: #e2e8f0;
    }
    
    .stTabs [aria-selected="true"]:hover {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the professional header section."""
    st.markdown("""
    <div class="header-container">
        <div class="header-title">🎧 AI Call Center Assistant</div>
        <div class="header-subtitle">Enterprise-grade call analysis with automated summarization and quality scoring</div>
    </div>
    """, unsafe_allow_html=True)

def render_quality_gauge(score, title, color="#3b82f6"):
    """Render a quality score gauge using Plotly."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [None, 10], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 4], 'color': "#fee2e2"},
                {'range': [4, 7], 'color': "#fef3c7"},
                {'range': [7, 10], 'color': "#dcfce7"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 8.0
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
        font={'color': "white", 'family': "Arial", 'size': 14},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def main():
    """Main Streamlit application."""
    
    # Inject custom CSS
    inject_custom_css()
    
    # Render header
    render_header()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv('OPENAI_API_KEY', ''),
            help="Required for transcription, summarization, and quality scoring"
        )
        
        langsmith_key = st.text_input(
            "LangSmith API Key (optional)",
            type="password", 
            value=os.getenv('LANGCHAIN_API_KEY', ''),
            help="For debugging traces in LangSmith - visit https://smith.langchain.com/"
        )
        
        if langsmith_key:
            os.environ["LANGCHAIN_API_KEY"] = langsmith_key
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
        
        if not openai_key:
            st.error("Please provide your OpenAI API key")
            return
    
    # Main content
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📤 Upload Call Data")
        st.write("Select an audio file or transcript to begin analysis")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['mp3', 'wav', 'm4a', 'txt'],
            help="Audio files (.mp3, .wav, .m4a) or text transcripts (.txt)"
        )
        
        if uploaded_file:
            file_size = len(uploaded_file.getvalue()) / 1024 / 1024  # MB
            st.success(f"✅ **{uploaded_file.name}** ({file_size:.1f} MB)")
            
            if st.button("🚀 Process Call", type="primary", use_container_width=True):
                # Process the file
                try:
                    # Create workflow
                    workflow = CallCenterWorkflow(
                        openai_api_key=openai_key
                    )
                    
                    # Determine input type and content
                    file_extension = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
                    audio_extensions = ['mp3', 'wav', 'm4a', 'ogg', 'webm']
                    
                    
                    if uploaded_file.type.startswith('audio/') or file_extension in audio_extensions:
                        input_type = InputType.AUDIO
                        content = uploaded_file.read()
                    else:
                        input_type = InputType.TRANSCRIPT
                        try:
                            content = uploaded_file.read().decode('utf-8')
                        except UnicodeDecodeError:
                            st.error("❌ Unable to read text file. Please ensure it's a valid text file.")
                            return
                    
                    # Create input
                    call_input = CallInput(
                        input_type=input_type,
                        content=content,
                        file_name=uploaded_file.name
                    )
                    
                    # Process through workflow
                    with st.spinner("Processing call... This may take a moment."):
                        result = workflow.process_call(call_input)
                    
                    # Store result in session state
                    st.session_state.result = result
                    st.success("✅ Processing complete!")
                    
                except Exception as e:
                    st.error(f"❌ Processing failed: {str(e)}")
    
    with col2:
        st.subheader("📊 Analysis Results")
        
        if hasattr(st.session_state, 'result') and st.session_state.result:
            result = st.session_state.result
            
            # Status display at the top
            status_emoji = {"success": "✅", "partial": "⚠️", "failed": "❌"}.get(result.status, "❓")
            st.info(f"{status_emoji} Processing {result.status.upper()} ({result.processing_time_seconds:.1f}s)")
            
            # Tabbed interface
            tab1, tab2, tab3 = st.tabs(["📝 Call Summary", "📊 Quality Assessment", "📄 Transcript"])
            
            with tab1:
                # Call Summary tab content
                if result.summary:
                    st.write(result.summary.summary)
                    
                    # Key Points - only show if they exist
                    if result.summary.key_points:
                        st.markdown("**🔑 Key Points:**")
                        for point in result.summary.key_points:
                            st.markdown(f"• {point}")
                    
                    # Sentiment and Outcome
                    col_sentiment, col_outcome = st.columns(2)
                    with col_sentiment:
                        # Fix sentiment emoji
                        sentiment_emojis = {
                            "positive": "😊",
                            "neutral": "😐", 
                            "negative": "😔"
                        }
                        emoji = sentiment_emojis.get(result.summary.sentiment.lower(), "😐")
                        st.metric("Sentiment", f"{emoji} {result.summary.sentiment.title()}")
                    
                    with col_outcome:
                        st.metric("Outcome", f"🎯 {result.summary.outcome}")
                else:
                    st.info("No summary available for this call.")
            
            with tab2:
                # Quality Assessment tab content
                if result.quality_score:
                    # Quality gauge visualizations
                    col_overall, col_empathy, col_resolution = st.columns(3)
                    
                    with col_overall:
                        fig_overall = render_quality_gauge(
                            result.quality_score.overall_score,
                            "Overall Score",
                            "#3b82f6"
                        )
                        st.plotly_chart(fig_overall, use_container_width=True)
                    
                    with col_empathy:
                        fig_empathy = render_quality_gauge(
                            result.quality_score.empathy_score,
                            "Empathy Score", 
                            "#10b981"
                        )
                        st.plotly_chart(fig_empathy, use_container_width=True)
                    
                    with col_resolution:
                        fig_resolution = render_quality_gauge(
                            result.quality_score.resolution_score,
                            "Resolution Score",
                            "#f59e0b"
                        )
                        st.plotly_chart(fig_resolution, use_container_width=True)
                    
                    # Feedback
                    if result.quality_score.feedback:
                        st.markdown("**💬 Performance Feedback:**")
                        st.write(result.quality_score.feedback)
                else:
                    st.info("No quality assessment available for this call.")
            
            with tab3:
                # Transcript tab content
                if result.transcript_text:
                    st.text(result.transcript_text)
                else:
                    st.info("No transcript available for this call.")
            
            # Errors (show in all tabs if present)
            if result.errors:
                st.warning("⚠️ Issues encountered:")
                for error in result.errors:
                    st.markdown(f"- **{error['agent']}**: {error['error']}")
        
        else:
            st.info("Upload and process a file to see results here.")


if __name__ == "__main__":
    main()