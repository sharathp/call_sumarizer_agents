"""
Modern Streamlit UI for AI Call Center Assistant.
"""

import os
import time
import streamlit as st
from dotenv import load_dotenv
import plotly.graph_objects as go

from utils.validation import CallInput, InputType
from workflow import CallCenterWorkflow

# Load environment variables
load_dotenv()

# Configure logging for UI
from config.settings import setup_logging
setup_logging()

# Page configuration
st.set_page_config(
    page_title="AI Call Center Assistant",
    page_icon="🎧",
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
        <div class="header-title"><i class="fas fa-headset"></i> AI Call Center Assistant</div>
        <div class="header-subtitle">Enterprise-grade call analysis with automated summarization and quality scoring</div>
    </div>
    """, unsafe_allow_html=True)

def render_quality_gauge(score, title, color="#3b82f6", dark_mode=None):
    """Render a quality score gauge using Plotly with adaptive colors."""
    # Auto-detect based on session state if not provided
    if dark_mode is None:
        dark_mode = st.session_state.get('dark_mode', True)  # Default to dark mode
    
    # Use adaptive colors based on theme
    if dark_mode:
        # Dark mode: light text on dark background
        text_color = "#e2e8f0"  # Light gray
        tick_color = "#94a3b8"  # Medium gray
        bg_color = "rgba(30, 41, 59, 0.3)"  # Dark semi-transparent
        steps_colors = [
            {'range': [0, 4], 'color': "rgba(239, 68, 68, 0.3)"},  # Red
            {'range': [4, 7], 'color': "rgba(251, 146, 60, 0.3)"},  # Orange
            {'range': [7, 10], 'color': "rgba(34, 197, 94, 0.3)"}  # Green
        ]
    else:
        # Light mode: dark text on light background
        text_color = "#1e293b"  # Dark gray
        tick_color = "#64748b"  # Medium dark gray
        bg_color = "rgba(241, 245, 249, 0.5)"  # Light semi-transparent
        steps_colors = [
            {'range': [0, 4], 'color': "rgba(254, 226, 226, 0.8)"},  # Light red
            {'range': [4, 7], 'color': "rgba(254, 243, 199, 0.8)"},  # Light orange
            {'range': [7, 10], 'color': "rgba(220, 252, 231, 0.8)"}  # Light green
        ]
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 16, 'color': text_color}},
        number = {'font': {'size': 32, 'color': text_color}, 'suffix': "/10"},
        gauge = {
            'axis': {
                'range': [0, 10], 
                'tickwidth': 2, 
                'tickcolor': tick_color, 
                'tickfont': {'size': 12, 'color': tick_color},
                'tickmode': 'linear',
                'tick0': 0,
                'dtick': 2
            },
            'bar': {'color': color, 'thickness': 0.4},
            'bgcolor': bg_color,
            'borderwidth': 2,
            'bordercolor': tick_color,
            'steps': steps_colors
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        font={'color': text_color, 'family': "Arial", 'size': 12},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def main():
    """Main Streamlit application."""
    
    # Initialize dark mode in session state if not present
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True  # Default to dark mode
    
    # Add Font Awesome
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">',
        unsafe_allow_html=True
    )

    # Add JavaScript for browser color scheme detection
    st.markdown("""
    <script>
    // Detect browser's preferred color scheme
    function detectColorScheme() {
        const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        // Store in a hidden div that Streamlit can read
        const indicator = document.getElementById('color-scheme-indicator');
        if (indicator) {
            indicator.textContent = isDark ? 'dark' : 'light';
        }
    }
    
    // Run on load and listen for changes
    window.addEventListener('DOMContentLoaded', detectColorScheme);
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', detectColorScheme);
    </script>
    <div id="color-scheme-indicator" style="display: none;"></div>
    """, unsafe_allow_html=True)

    # Inject custom CSS
    inject_custom_css()

    # Render header
    render_header()

    # Sidebar for configuration
    with st.sidebar:
        st.markdown('<i class="fas fa-cog" style="margin-right: 8px; font-size: 1.2em;"></i>**Configuration**', unsafe_allow_html=True)
        
        # Theme toggle
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Theme**")
        with col2:
            theme_icon = "🌙" if st.session_state.dark_mode else "☀️"
            if st.button(theme_icon, key="theme_toggle", help="Toggle dark/light mode"):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        
        st.markdown("---")
        
        deepgram_key = st.text_input(
            "Deepgram API Key",
            type="password",
            value=os.getenv('DEEPGRAM_API_KEY', ''),
            help="Required for transcription with speaker diarization"
        )
        
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv('OPENAI_API_KEY', ''),
            help="Required for summarization and quality scoring, optional fallback for transcription"
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
        
        if not deepgram_key:
            st.error("Please provide your Deepgram API key for transcription with speaker diarization")
            return
            
        if not openai_key:
            st.error("Please provide your OpenAI API key for LLM operations")
            return
    
    # Main content
    col1, col2 = st.columns([1, 2])
    
    # Initialize uploaded_file variable
    uploaded_file = None
    
    with col1:
        st.markdown('<i class="fas fa-upload" style="margin-right: 8px; font-size: 1.1em;"></i>**Upload Call Data**', unsafe_allow_html=True)
        st.write("Select an audio file or transcript to begin analysis")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['mp3', 'wav', 'm4a', 'txt'],
            help="Audio files (.mp3, .wav, .m4a) or text transcripts (.txt)"
        )
        
        # Reset UI state when a different file is uploaded
        if uploaded_file:
            # Check if this is a new file (different from the last processed one)
            current_file_id = f"{uploaded_file.name}_{len(uploaded_file.getvalue())}"
            if 'last_processed_file_id' not in st.session_state:
                st.session_state.last_processed_file_id = None
            
            if st.session_state.last_processed_file_id != current_file_id:
                # Clear previous results and UI state
                if 'result' in st.session_state:
                    del st.session_state.result
                if 'processing_complete' in st.session_state:
                    del st.session_state.processing_complete
                if 'progress_status' in st.session_state:
                    del st.session_state.progress_status
                    
                # Update the file ID
                st.session_state.last_processed_file_id = current_file_id
        
        if uploaded_file:
            file_size = len(uploaded_file.getvalue()) / 1024 / 1024  # MB
            st.markdown(f'<div style="padding: 0.75rem; background-color: #dcfce7; border: 1px solid #16a34a; border-radius: 0.5rem; color: #166534;"><i class="fas fa-check-circle"></i> **{uploaded_file.name}** ({file_size:.1f} MB)</div>', unsafe_allow_html=True)
            
            process_button = st.button(
                "🚀 Process Call", 
                type="primary", 
                use_container_width=True,
                help="Start processing the uploaded file"
            )
            
            if process_button:
                # Process the file
                try:
                    # Create workflow
                    workflow = CallCenterWorkflow(
                        openai_api_key=openai_key,
                        deepgram_api_key=deepgram_key
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
                    
                    # Process through workflow with detailed progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    timing_text = st.empty()
                    
                    # Track timing for each step
                    step_times = {}
                    overall_start = time.time()
                    
                    # Step 1: Initialize
                    init_start = time.time()
                    status_text.markdown('<i class="fas fa-rocket"></i> Initializing workflow...', unsafe_allow_html=True)
                    progress_bar.progress(10)
                    time.sleep(0.5)
                    step_times["initialize"] = time.time() - init_start
                    timing_text.markdown(f"<small>Initialize: {step_times['initialize']:.1f}s</small>", unsafe_allow_html=True)
                    
                    # Step 2: Transcription
                    transcription_start = time.time()
                    if input_type == InputType.AUDIO:
                        status_text.markdown('<i class="fas fa-microphone"></i> Transcribing audio...', unsafe_allow_html=True)
                        progress_bar.progress(25)
                    else:
                        status_text.markdown('<i class="fas fa-file-text"></i> Processing transcript...', unsafe_allow_html=True)
                        progress_bar.progress(25)
                    
                    # Start processing in background
                    import threading
                    result_container = {"result": None, "error": None}
                    
                    def process_workflow():
                        try:
                            result_container["result"] = workflow.process_call(call_input)
                        except Exception as e:
                            result_container["error"] = e
                    
                    # Start processing
                    thread = threading.Thread(target=process_workflow)
                    thread.start()
                    
                    # Transcription phase
                    transcription_complete = False
                    for i in range(8):
                        if not thread.is_alive():
                            transcription_complete = True
                            break
                        time.sleep(0.5)
                        if result_container["error"]:
                            break
                    
                    if not transcription_complete:
                        step_times["transcription"] = time.time() - transcription_start
                        timing_text.markdown(f"<small>Initialize: {step_times['initialize']:.1f}s | Transcription: {step_times['transcription']:.1f}s</small>", unsafe_allow_html=True)
                    
                    if thread.is_alive():
                        summarization_start = time.time()
                        status_text.markdown('<i class="fas fa-edit"></i> Summarizing call content...', unsafe_allow_html=True)
                        progress_bar.progress(55)
                        
                        # Summarization phase
                        summarization_complete = False
                        for i in range(8):
                            if not thread.is_alive():
                                summarization_complete = True
                                break
                            time.sleep(0.5)
                            if result_container["error"]:
                                break
                        
                        if not summarization_complete:
                            step_times["summarization"] = time.time() - summarization_start
                            timing_display = f"Initialize: {step_times['initialize']:.1f}s"
                            if "transcription" in step_times:
                                timing_display += f" | Transcription: {step_times['transcription']:.1f}s"
                            timing_display += f" | Summarization: {step_times['summarization']:.1f}s"
                            timing_text.markdown(f"<small>{timing_display}</small>", unsafe_allow_html=True)
                    
                    if thread.is_alive():
                        quality_start = time.time()
                        status_text.markdown('<i class="fas fa-bullseye"></i> Assessing call quality...', unsafe_allow_html=True)
                        progress_bar.progress(80)
                        
                        # Quality scoring phase
                        for i in range(8):
                            if not thread.is_alive():
                                break
                            time.sleep(0.5)
                            if result_container["error"]:
                                break
                        
                        step_times["quality_scoring"] = time.time() - quality_start
                    
                    # Wait for completion
                    while thread.is_alive():
                        time.sleep(0.1)
                    
                    # Check for retry scenarios
                    if result_container["result"] and result_container["result"].errors:
                        retry_start = time.time()
                        status_text.markdown('<i class="fas fa-redo"></i> Retrying failed components...', unsafe_allow_html=True)
                        progress_bar.progress(90)
                        time.sleep(1)
                        step_times["retry"] = time.time() - retry_start
                    
                    # Finalize
                    status_text.markdown('<i class="fas fa-check-circle"></i> Processing complete!', unsafe_allow_html=True)
                    progress_bar.progress(100)
                    
                    # Show final timing breakdown
                    total_time = time.time() - overall_start
                    timing_display = f"**Total: {total_time:.1f}s** | "
                    timing_parts = []
                    if "transcription" in step_times:
                        timing_parts.append(f"Transcription: {step_times['transcription']:.1f}s")
                    if "summarization" in step_times:
                        timing_parts.append(f"Summarization: {step_times['summarization']:.1f}s")
                    if "quality_scoring" in step_times:
                        timing_parts.append(f"Quality: {step_times['quality_scoring']:.1f}s")
                    if "retry" in step_times:
                        timing_parts.append(f"Retry: {step_times['retry']:.1f}s")
                    
                    timing_display += " | ".join(timing_parts)
                    timing_text.markdown(f"<small>{timing_display}</small>", unsafe_allow_html=True)
                    
                    time.sleep(1)
                    
                    # Clear progress indicators but keep timing
                    progress_bar.empty()
                    status_text.empty()
                    
                    if result_container["error"]:
                        raise result_container["error"]
                    
                    result = result_container["result"]
                    
                    # Store result in session state
                    st.session_state.result = result
                    st.markdown('<div style="padding: 0.75rem; background-color: #dcfce7; border: 1px solid #16a34a; border-radius: 0.5rem; color: #166534;"><i class="fas fa-check-circle"></i> Processing complete!</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.markdown(f'<div style="padding: 0.75rem; background-color: #fee2e2; border: 1px solid #dc2626; border-radius: 0.5rem; color: #dc2626;"><i class="fas fa-exclamation-triangle"></i> Processing failed: {str(e)}</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<i class="fas fa-chart-bar" style="margin-right: 8px; font-size: 1.1em;"></i>**Analysis Results**', unsafe_allow_html=True)
        
        # Check if we have results to display
        if hasattr(st.session_state, 'result') and st.session_state.result:
            result = st.session_state.result
            
            # Status display at the top
            status_icons = {
                "success": '<i class="fas fa-check-circle" style="color: green;"></i>',
                "partial": '<i class="fas fa-exclamation-triangle" style="color: orange;"></i>', 
                "failed": '<i class="fas fa-times-circle" style="color: red;"></i>'
            }
            status_icon = status_icons.get(result.status, '<i class="fas fa-question-circle"></i>')
            st.markdown(f'<div style="padding: 0.75rem; background-color: #dbeafe; border: 1px solid #3b82f6; border-radius: 0.5rem; color: #1e40af;">{status_icon} Processing {result.status.upper()} ({result.processing_time_seconds:.1f}s)</div>', unsafe_allow_html=True)
            
            # Determine summary tab label based on sentiment
            summary_tab_label = "Summary"
            if result.summary and hasattr(result.summary, 'sentiment'):
                sentiment_emojis = {
                    "positive": "😊",
                    "neutral": "😐",
                    "negative": "😔"
                }
                emoji = sentiment_emojis.get(result.summary.sentiment.lower(), "")
                if emoji:
                    summary_tab_label = f"{emoji} Summary"
            
            # Tabbed interface
            tab1, tab2, tab3 = st.tabs([
                "📄 Transcript",
                summary_tab_label,
                "📊 Quality Scores"
            ])
            
            with tab1:
                # Transcript tab content
                if result.transcript_text:
                    # Check if we have speaker segments for enhanced display
                    # Debug: Show speaker info
                    if hasattr(result, 'speakers'):
                        if result.speakers:
                            st.success(f"✅ Found {len(result.speakers)} speaker segments!")
                        else:
                            st.info("ℹ️ No speaker segments found - showing raw transcript")
                    else:
                        st.warning("⚠️ No speakers attribute in result")
                    
                    if hasattr(result, 'speakers') and result.speakers:
                        st.markdown("### 🗣️ Speaker-Segmented Conversation")
                        
                        # Show speaker statistics
                        speaker_stats = {}
                        total_duration = 0
                        for segment in result.speakers:
                            speaker = segment.speaker
                            duration = segment.end - segment.start
                            total_duration += duration
                            
                            if speaker not in speaker_stats:
                                speaker_stats[speaker] = {"count": 0, "duration": 0}
                            speaker_stats[speaker]["count"] += 1
                            speaker_stats[speaker]["duration"] += duration
                        
                        # Display speaker summary
                        cols = st.columns(len(speaker_stats))
                        for i, (speaker, stats) in enumerate(speaker_stats.items()):
                            with cols[i]:
                                talk_percentage = (stats["duration"] / total_duration * 100) if total_duration > 0 else 0
                                st.metric(
                                    label=f"🗣️ {speaker}",
                                    value=f"{stats['count']} segments",
                                    delta=f"{talk_percentage:.1f}% talk time"
                                )
                        
                        # Display speaker segments in a formatted way
                        transcript_html = ""
                        for i, segment in enumerate(result.speakers):
                            # Determine speaker color
                            speaker_num = segment.speaker.replace("Speaker ", "")
                            colors = ["#e3f2fd", "#f3e5f5", "#e8f5e8", "#fff3e0", "#fce4ec"]
                            bg_color = colors[int(speaker_num) % len(colors)]
                            
                            # Format timing
                            start_time = f"{segment.start:.1f}s"
                            end_time = f"{segment.end:.1f}s"
                            
                            # Create speaker segment HTML
                            transcript_html += f"""
                            <div style="
                                margin: 8px 0; 
                                padding: 12px; 
                                background-color: {bg_color}; 
                                border-left: 4px solid #1976d2; 
                                border-radius: 6px;
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            ">
                                <div style="
                                    display: flex; 
                                    justify-content: space-between; 
                                    align-items: center; 
                                    margin-bottom: 6px;
                                ">
                                    <strong style="color: #1976d2; font-size: 14px;">
                                        🗣️ {segment.speaker}
                                    </strong>
                                    <span style="
                                        font-size: 12px; 
                                        color: #666; 
                                        background: rgba(255,255,255,0.7); 
                                        padding: 2px 8px; 
                                        border-radius: 12px;
                                    ">
                                        {start_time} - {end_time}
                                    </span>
                                </div>
                                <div style="
                                    line-height: 1.5; 
                                    color: #333;
                                    font-size: 14px;
                                ">
                                    {segment.text}
                                </div>
                            </div>
                            """
                        
                        # Display the formatted conversation
                        st.markdown(transcript_html, unsafe_allow_html=True)
                        
                        # Show raw transcript as expandable section
                        with st.expander("📄 View Raw Transcript"):
                            st.text_area(
                                "Full Transcript",
                                value=result.transcript_text,
                                height=300,
                                disabled=True,
                                label_visibility="collapsed"
                            )
                    else:
                        # Fallback to regular transcript display
                        st.text_area(
                            "Call Transcript",
                            value=result.transcript_text,
                            height=400,
                            disabled=True,
                            label_visibility="collapsed"
                        )
                else:
                    st.info("No transcript available for this call.")
            
            with tab2:
                # Call Summary tab content
                if result.summary:
                    st.write(result.summary.summary)
                    
                    # Key Points - only show if they exist
                    if result.summary.key_points:
                        st.markdown('**<i class="fas fa-key" style="margin-right: 8px;"></i>Key Points:**', unsafe_allow_html=True)
                        for point in result.summary.key_points:
                            st.markdown(f"• {point}")
                else:
                    st.info("No summary available for this call.")
            
            with tab3:
                # Quality Assessment tab content
                if result.quality_score:
                    # Quality gauge visualizations
                    col_tone, col_professionalism, col_resolution = st.columns(3)
                    
                    with col_tone:
                        fig_tone = render_quality_gauge(
                            result.quality_score.tone_score,
                            "Tone Score",
                            "#3b82f6",
                            dark_mode=st.session_state.dark_mode
                        )
                        st.plotly_chart(fig_tone, use_container_width=True)
                    
                    with col_professionalism:
                        fig_professionalism = render_quality_gauge(
                            result.quality_score.professionalism_score,
                            "Professionalism", 
                            "#10b981",
                            dark_mode=st.session_state.dark_mode
                        )
                        st.plotly_chart(fig_professionalism, use_container_width=True)
                    
                    with col_resolution:
                        fig_resolution = render_quality_gauge(
                            result.quality_score.resolution_score,
                            "Resolution Score",
                            "#f59e0b",
                            dark_mode=st.session_state.dark_mode
                        )
                        st.plotly_chart(fig_resolution, use_container_width=True)
                    
                    # Feedback
                    if result.quality_score.feedback:
                        st.markdown('**<i class="fas fa-comment" style="margin-right: 8px;"></i>Performance Feedback:**', unsafe_allow_html=True)
                        st.write(result.quality_score.feedback)
                else:
                    st.info("No quality assessment available for this call.")
            
            # Errors (show in all tabs if present)
            if result.errors:
                st.markdown('<div style="padding: 0.75rem; background-color: #fef3c7; border: 1px solid #f59e0b; border-radius: 0.5rem; color: #92400e;"><i class="fas fa-exclamation-triangle"></i> Issues encountered:</div>', unsafe_allow_html=True)
                for error in result.errors:
                    st.markdown(f"- **{error['agent']}**: {error['error']}")
        
        else:
            if uploaded_file:
                st.info("Click 'Process Call' to analyze the uploaded file.")
            else:
                st.info("Upload and process a file to see results here.")


if __name__ == "__main__":
    main()