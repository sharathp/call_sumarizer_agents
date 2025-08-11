"""
Simplified Streamlit UI for AI Call Center Assistant.
"""

import os
import streamlit as st
from dotenv import load_dotenv

from utils.validation import CallInput, InputType
from workflow import CallCenterWorkflow

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Call Center Assistant",
    page_icon="📞",
    layout="wide"
)


def main():
    """Main Streamlit application."""
    
    # Header
    st.title("📞 AI Call Center Assistant")
    st.markdown("Upload a call recording or transcript to get an automated summary and quality assessment")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv('OPENAI_API_KEY', ''),
            help="Required for transcription, summarization, and quality scoring"
        )
        
        if not openai_key:
            st.error("Please provide your OpenAI API key")
            return
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['mp3', 'wav', 'm4a', 'txt'],
            help="Audio files (.mp3, .wav, .m4a) or text transcripts (.txt)"
        )
        
        if uploaded_file:
            st.success(f"File uploaded: {uploaded_file.name}")
            
            if st.button("🚀 Process Call", type="primary"):
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
        st.subheader("📊 Results")
        
        if hasattr(st.session_state, 'result') and st.session_state.result:
            result = st.session_state.result
            
            # Status
            status_emoji = {
                "success": "✅",
                "partial": "⚠️", 
                "failed": "❌"
            }.get(result.status, "❓")
            
            st.metric("Status", f"{status_emoji} {result.status.upper()}")
            st.metric("Processing Time", f"{result.processing_time_seconds:.2f}s")
            
            # Summary
            if result.summary:
                st.markdown("**📝 Summary:**")
                st.write(result.summary.summary)
                
                st.markdown("**🔑 Key Points:**")
                for point in result.summary.key_points:
                    st.markdown(f"• {point}")
                
                col_sentiment, col_outcome = st.columns(2)
                with col_sentiment:
                    sentiment_color = {
                        "positive": "green",
                        "neutral": "gray", 
                        "negative": "red"
                    }.get(result.summary.sentiment, "gray")
                    st.markdown(f"**Sentiment:** :{sentiment_color}[{result.summary.sentiment.upper()}]")
                
                with col_outcome:
                    st.markdown(f"**Outcome:** {result.summary.outcome}")
            
            # Quality Score
            if result.quality_score:
                st.markdown("**📊 Quality Assessment:**")
                
                col_overall, col_empathy, col_resolution = st.columns(3)
                with col_overall:
                    st.metric("Overall", f"{result.quality_score.overall_score:.1f}/10")
                with col_empathy:
                    st.metric("Empathy", f"{result.quality_score.empathy_score:.1f}/10")
                with col_resolution:
                    st.metric("Resolution", f"{result.quality_score.resolution_score:.1f}/10")
                
                st.markdown("**💬 Feedback:**")
                st.write(result.quality_score.feedback)
            
            # Transcript (if available)
            if result.transcript_text:
                with st.expander("📄 View Transcript"):
                    st.text(result.transcript_text)
            
            # Errors (if any)
            if result.errors:
                st.warning("⚠️ Issues encountered:")
                for error in result.errors:
                    st.markdown(f"- **{error['agent']}**: {error['error']}")
        
        else:
            st.info("Upload and process a file to see results here.")


if __name__ == "__main__":
    main()