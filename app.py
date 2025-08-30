import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import json
import time
import re
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
from model import Model
from context_extractor import ContextExtractor
from agent import KriarLearningAgent
from tools import tools
from streamlit_player import st_player

st.set_page_config(
    page_title="KRIAR -Learning Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://images.pexels.com/photos/821644/pexels-photo-821644.jpeg");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
}
</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        background-color: #000000 !important; /* pure black */
        color: white; /* white text for contrast */
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <style>
    .context-info {
        background: rgba(0, 0, 0, 0.6); /* semi-transparent dark */
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        color: #f1f1f1;
        font-family: 'Segoe UI', sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.6);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .context-info:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.8);
    }

    .context-info h4 {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #ffd369; /* highlight color */
    }

    .context-info p {
        font-size: 0.95rem;
        margin: 0.3rem 0;
        line-height: 1.4;
    }

    .context-info strong {
        color: #ff8c00; /* orange highlight for labels */
    }
    </style>
    """,
    unsafe_allow_html=True
)

def load_css():
    st.markdown("""
    <style>
    # /* 🌌 Space Gradient Background */
    # body {
    #     background: radial-gradient(ellipse at top, #0d0d1a 0%, #000000 100%);
    #     background-attachment: fixed;
    #     color: #ffffff;
    # }
    # .stApp {
    #     background: radial-gradient(circle at 20% 20%, rgba(30,30,60,0.9), rgba(0,0,0,1)),
    #                 radial-gradient(circle at 80% 80%, rgba(60,20,60,0.8), rgba(0,0,0,1));
    #     background-blend-mode: screen;
    # }

    /* Section headers */
    .section-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #fff;
        background: transparent;
        text-align: center;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.6);
    }

    /* Floating card style (glassmorphism but darker) */
    .chat-message,
    .sidebar-section,
    .video-container,
    .stats-container {
        background: rgba(10, 10, 20, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 14px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.7);
        padding: 1rem;
    }

    /* User & Assistant messages */
    .user-message { border-left: 4px solid #00c6ff; }
    .assistant-message { border-left: 4px solid #ff4ecd; }

    /* Scroll area */
    .chat-scroll {
        max-height: 400px;
        overflow-y: auto;
        background: rgba(0,0,0,0.6);
        border-radius: 10px;
        padding: 0.8rem;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #6a11cb, #2575fc);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        border: none;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0,0,0,0.6);
    }

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea {
        background: rgba(20,20,30,0.7);
        color: #fff !important;
        border-radius: 8px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)




@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: datetime
    type: str = "text"
    video_timestamp: float = 0.0

@dataclass
class VideoSession:
    video_id: str
    title: str
    url: str
    start_time: datetime
    messages: List[ChatMessage]

class KriarLearningAssistant:
    def __init__(self):
        self.initialize_session_state()
        self.initialize_agent()

    def initialize_session_state(self):
        """Initialize all session state variables"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        if 'code_history' not in st.session_state:
            st.session_state.code_history = []

        if 'current_video' not in st.session_state:
            st.session_state.current_video = None

        if 'video_sessions' not in st.session_state:
            st.session_state.video_sessions = []

        if 'current_timestamp' not in st.session_state:
            st.session_state.current_timestamp = 0.0

        if 'context_extractor' not in st.session_state:
            st.session_state.context_extractor = None

        if 'agent' not in st.session_state:
            st.session_state.agent = None
        if 'event' not in st.session_state:
            st.session_state.event = None
        if 'video_url' not in st.session_state:
            st.session_state.video_url = None
        
        if 'api_key' not in st.session_state:
            st.session_state.api_key = None
        if 'model_provider' not in st.session_state:
            st.session_state.model_provider = None
        if 'model_name' not in st.session_state:
            st.session_state.model_name = None
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {
                'auto_timestamp': True,
                'response_length': 'medium',
                'model_provider': st.session_state.model_provider,
                'model_name': st.session_state.model_name
            }

    def initialize_agent(self):
        """Initialize the learning agent"""
        try:
            if st.session_state.agent is None:
                if st.session_state.model_provider and st.session_state.model_name and st.session_state.api_key:
                    preferences = st.session_state.user_preferences
                    st.session_state.agent = KriarLearningAgent(
                        model_provider=st.session_state.model_provider,
                        model_name=st.session_state.model_name,
                        api_key=st.session_state.api_key
                    )
        except Exception as e:
            st.error(f"Error initializing AI agent: {e}")
    def initialize_contextextractor(self,url,target_timestamp):
        try:
            if st.session_state.context_extractor is None:
                st.session_state.context_extractor = ContextExtractor(url,target_timestamp=target_timestamp)
        except Exception as e:
            st.error(f"Error initializing context extractor: {e}")
    def get_timestamp(self):
        return ""
    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL"""
        try:
            parsed_url = urlparse(url)
            if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
                return parse_qs(parsed_url.query)['v'][0]
            elif parsed_url.hostname == 'youtu.be':
                return parsed_url.path[1:]
            return ""
        except:
            return ""
    def render_sidebar(self):
        """Render sidebar with conversation history and settings"""
        with st.sidebar:
            st.markdown('<div class="section-header">📚 Learning Sessions</div>', unsafe_allow_html=True)

            total_sessions = len(st.session_state.video_sessions)
            total_questions = len(st.session_state.chat_history)
            total_code_snippets = len(st.session_state.code_history)

            st.markdown(f"""
            <div class="stats-container">
                <h4>📊 Session Stats</h4>
                <p>🎥 Videos: {total_sessions}</p>
                <p>❓ Questions: {total_questions}</p>
                <p>💻 Code Snippets: {total_code_snippets}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.current_video and st.session_state.context_extractor:
                metadata = st.session_state.context_extractor.metadata
                st.markdown(f"""
                <div class="context-info">
                    <h4>📹 Current Video</h4>
                    <p><strong>Title:</strong> {metadata.get('title', 'Unknown')[:50]}...</p>
                    <p><strong>Author:</strong> {metadata.get('author', 'Unknown')}</p>
                    <p><strong>Length:</strong> {metadata.get('length', 'Unknown')}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="section-header">💬 Recent Conversations</div>', unsafe_allow_html=True)

            if st.session_state.chat_history:
                for i, msg in enumerate(st.session_state.chat_history[-3:]):
                    with st.container():
                        st.markdown(f"""
                        <div class="sidebar-section">
                            <strong>{'🧑 You' if msg.role == 'user' else '🤖 Assistant'}:</strong><br>
                            <span style="font-size: 0.9rem;">{msg.content[:80]}...</span><br>
                            <span class="timestamp">{msg.timestamp.strftime('%H:%M')}</span>
                            {f'<div class="timestamp-info">📍 @{msg.video_timestamp}s</div>' if msg.video_timestamp > 0 else ''}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No conversations yet. Load a video and start asking questions!")


            st.markdown('<div class="section-header">⚙️ Settings</div>', unsafe_allow_html=True)

            st.session_state.user_preferences['auto_timestamp'] = st.checkbox(
                "Auto-use current timestamp", 
                value=st.session_state.user_preferences['auto_timestamp']
            )

            st.session_state.user_preferences['response_length'] = st.selectbox(
                "Response Length",
                ['short', 'medium', 'detailed'],
                index=['short', 'medium', 'detailed'].index(st.session_state.user_preferences['response_length'])
            )

            
            st.markdown("### Settings")
            if st.button("🔄 Reset Settings"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
                          

    def render_video_section(self):
        """Render the main video section"""

        if not st.session_state.get("video_loaded", False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                video_url = st.text_input(
                    "Enter YouTube URL:",
                    placeholder="https://www.youtube.com/watch?v=VIDEO_ID",
                    help="Paste any YouTube video URL here to start learning",
                    key="video_url_input"
                )
                st.session_state.video_url = video_url

            with col2:
                enter_api_key = st.text_input(
                    "Enter API Key",
                    key="api_key_input",
                    type="password"
                )
                st.session_state.api_key = enter_api_key
            with col3:
                model_provider = st.selectbox("Choose a model provider:", [ "groq", "google"])
                options = {"groq": ["openai/gpt-oss-20b","openai/gpt-oss-120b","deepseek-r1-distill-llama-70b","llama-3.3-70b-versatile"], "google": "gemini-2.5-pro"}
                item = st.selectbox("Choose an item:", options[model_provider])
                st.session_state.model_provider = model_provider
                st.session_state.model_name = item
            with col4:    
                load_video = st.button("🔄 Load Video", use_container_width=True)


            if load_video and video_url and enter_api_key and model_provider:
                
                context_extractor = ContextExtractor(video_url)
                st.session_state.context_extractor = context_extractor
                video_id = context_extractor.extract_youtube_video_id(video_url)
                if video_id:
                    try:
                        with st.spinner("🔄 Loading video and extracting transcript..."):

         
                            st.session_state.current_video = {
                                'id': video_id,
                                'url': video_url,
                                'loaded_at': datetime.now(),
                                'metadata': context_extractor.extract_metadata()
                            }

                            st.session_state.video_loaded = True 
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error loading video: {str(e)}")
                else:
                    st.error("❌ Invalid YouTube URL. Please check and try again.")
       

        if st.session_state.current_video:
            video_id = st.session_state.current_video['id']
            event = st.session_state.event
            video_url = st.session_state.video_url


            if event is None:
                event = st_player(
                    video_url,
                    events=["onProgress"],
                    progress_interval=1000,
                    key="youtube",
                    height=600,   
                    
                )
                st.session_state.event = event
            else:
                event = st_player(
                    video_url,
                    events=["onProgress"],
                    progress_interval=1000,
                    key="youtube",
                    height=600,   
                       
                )

            st.session_state.event = event
            if st.session_state.event.name == "onProgress":
                st.session_state.current_timestamp = st.session_state.event.data.get("playedSeconds", 0)
            else:
                st.session_state.current_timestamp = 0


            if st.session_state.context_extractor:
                metadata = st.session_state.context_extractor.metadata
                st.markdown(f"""
                <div class="context-info">
                    <h4>📹 {metadata.get('title', 'Video Title')}</h4>
                    <p><strong>Channel:</strong> {metadata.get('author', 'Unknown')}</p>
                    <p><strong>Duration:</strong> {metadata.get('length', 'Unknown')}</p>
                    <p><strong>Description:</strong> {metadata.get('description', 'No description available')}...</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="warning-box">
                <h4>🎬 No Video Loaded</h4>
                <p>Please enter a YouTube URL above to start learning with context-aware AI assistance!</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>🎯 Timestamp-based context extraction</li>
                    <li>🤖 AI answers based on video content</li>
                    <li>📝 Automatic transcript analysis</li>
                    <li>💡 Smart learning assistance</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        

    def render_chat_section(self):
        """Render the Q&A chat section"""
        st.markdown('<div class="section-header">💬 Context-Aware Q&A</div>', unsafe_allow_html=True)


        chat_container = st.container(height=400)
        with chat_container:
            if st.session_state.chat_history:
                for msg in st.session_state.chat_history:
                    css_class = "user-message" if msg.role == "user" else "assistant-message"
                    icon = "🧑" if msg.role == "user" else "🤖"
                    if st.session_state.event.name == "onProgress":
                        timestamp_info = st.session_state.event.data.get("playedSeconds", 0)
                    st.markdown(
                        f"""
                        <div class="chat-message {css_class}">
                            <strong>{icon} {msg.role.title()}:</strong><br>
                            {msg.content}<br>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:
                st.markdown("""
                <div class="success-box">
                    <h4>🚀 Smart Learning with Context!</h4>
                    <p>Ask questions about the video content. The AI will use the transcript and your current timestamp for accurate answers.</p>
                   
                    
                </div>
                """, unsafe_allow_html=True)


        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                user_question = st.text_area(
                    "Your Question:",
                    placeholder="Ask about the video content at current timestamp...",
                    height=80,
                    key="user_question_input"
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                submit_chat = st.form_submit_button("🚀 Ask", use_container_width=True)

                use_timestamp = st.checkbox(
                    "Use current timestamp", 
                    value=st.session_state.user_preferences['auto_timestamp']
                )


        if submit_chat and user_question:
            if not st.session_state.current_video:
                st.warning("⚠️ Please load a video first to enable context-aware responses!")
                return


            timestamp  = st.session_state.event.data.get("playedSeconds", 0)
            st.write(f"Timestamp used: {timestamp}")

            user_msg = ChatMessage(
                role="user",
                content=user_question,
                timestamp=datetime.now(),
                type="text",
                video_timestamp=timestamp
            )
            st.session_state.chat_history.append(user_msg)


            with st.spinner("🤔 Analyzing video context and generating response..."):
                try:
                    if st.session_state.agent and st.session_state.context_extractor:
                        response = st.session_state.agent.execute_task(
                            query=user_question,
                            video_url=st.session_state.current_video['url'],
                            timestamp=timestamp
                        ).strip()
                    else:
                        response = "Agent not available. Please check your configuration."

                except Exception as e:
                    response = f"Error generating response: {str(e)}"

            assistant_msg = ChatMessage(
                role="assistant", 
                content=response,
                timestamp=datetime.now(),
                type="text",
                video_timestamp=timestamp
            )
            st.session_state.chat_history.append(assistant_msg)

            st.rerun()

    def render_code_section(self):
        """Render the code assistance section"""
        st.markdown('<div class="section-header">💻 Code Assistant</div>', unsafe_allow_html=True)


        st.markdown("**📝 Your Code:**")
        user_code = st.text_area(
                "Enter your code here:",
                placeholder="# Use one space for indentation \n #Enter your Python code here...\nimport numpy as np\n\ndef my_function():\n    pass \n ",
                height=200,
                key="user_code_input"
        )

        
        st.markdown("**🎯 Code Actions:**")

        if st.button("🔍 Review Code", use_container_width=True):
                if user_code.strip():
                    with st.spinner("Analyzing code..."):
                        try:
                            if st.session_state.agent and st.session_state.context_extractor:
                                response = st.session_state.agent.execute_task(
                                    query=f"Review this code and provide suggestions: {user_code}",
                                    video_url=st.session_state.current_video['url'] if st.session_state.current_video else None,
                                    timestamp=st.session_state.current_timestamp
                                )
                            else:
                                response = "Code looks good! Consider adding comments and error handling."
                        except Exception as e:
                            response = f"Error reviewing code: {str(e)}"

                    code_msg = ChatMessage(
                        role="assistant",
                        content=f"**Code Review:**\n\n{response}",
                        timestamp=datetime.now(),
                        type="code"
                    )
                    st.session_state.code_history.append({
                        'original_code': user_code,
                        'review': response,
                        'timestamp': datetime.now()
                    })
                    st.session_state.chat_history.append(code_msg)
                    st.success("✅ Code reviewed!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Please enter some code first!")

        if st.button("🚀 Get Help", use_container_width=True):
                if user_code.strip():
                    with st.spinner("Getting help..."):
                        try:
                            if st.session_state.agent:
                                response = st.session_state.agent.execute_task(
                                    query=f"Help me understand and improve this code: {user_code}",
                                    video_url=st.session_state.current_video['url'] if st.session_state.current_video else None,
                                    timestamp=st.session_state.current_timestamp
                                )
                            else:
                                response = "Here are some general tips for improving your code structure and readability."
                        except Exception as e:
                            response = f"Error getting help: {str(e)}"

                    code_msg = ChatMessage(
                        role="assistant",
                        content=f"**Code Help:**\n\n{response}",
                        timestamp=datetime.now(),
                        type="code"
                    )
                    st.session_state.chat_history.append(code_msg)
                    st.success("💡 Help provided!")
                    time.sleep(1)
                    st.rerun()

    
        st.selectbox(
                "Programming Language:",
                ["Python", "JavaScript", "Java", "C++", "Go", "Rust"],
                key="code_language"
            )


        if st.session_state.code_history:
            with st.expander("📚 Code History", expanded=False):
                for i, entry in enumerate(st.session_state.code_history[-3:]):
                    st.markdown(f"""
                    <div class="context-info">
                        <h5>Code Snippet #{len(st.session_state.code_history) - len(st.session_state.code_history[-3:]) + i + 1}</h5>
                        <p><strong>Timestamp:</strong> {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <details>
                            <summary>View Code</summary>
                            <pre><code>{entry['original_code'][:200]}...</code></pre>
                        </details>
                        <p><strong>Review:</strong> {entry['review'][:200]}...</p>
                    </div>
                    """, unsafe_allow_html=True)

    def run(self):
        """Main application runner"""
        load_css()

        st.markdown('<h1 class="main-header">📚 Kriar - Learning Assistant</h1>', unsafe_allow_html=True)
        st.markdown("*An AI Learning Assistant for YouTube Lectures*")

        self.render_sidebar()

        main_col1, main_col2 = st.columns([2, 1])

        with main_col1:
            self.render_video_section()

        with main_col2:
            tab1, tab2 = st.tabs(["💬 Q&A Chat", "💻 Code Assistant"])

            with tab1:
                self.render_chat_section()

            with tab2:
                self.render_code_section()


def main():
    try:
        app = KriarLearningAssistant()
        app.run()
    except Exception as e:
        st.error(f"Application Error: {str(e)}")

        st.markdown("""
        ### 🔧 Troubleshooting

        **Common Issues:**
        1. **Missing API Keys:** Make sure your `.env` file contains valid API keys
        2. **Video Loading Issues:** Some videos may not have transcripts available
        3. **Model Provider Issues:** Check your model provider settings in the sidebar

        **Quick Fixes:**
        - Refresh the page
        - Check your internet connection
        - Verify YouTube URL is valid and public
        """)

if __name__ == "__main__":
    main()
