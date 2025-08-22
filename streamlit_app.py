import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
from src.blog_post_generator_workflow import workflow
from src.models import FinalBlogPost

load_dotenv()

# --- App Configuration ---
st.set_page_config(
    page_title="Agentic Blog Post Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load Custom CSS ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Session State Initialization ---
if "final_post" not in st.session_state:
    st.session_state.final_post = None
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "tone" not in st.session_state:
    st.session_state.tone = "Informative and engaging"
if "generate" not in st.session_state:
    st.session_state.generate = False

# --- Sidebar ---
with st.sidebar:
    st.title("📝 Agentic Blog Post Generator")
    st.subheader("Settings")
    st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), key="openai_api_key", type="password")
    st.text_input("Tavily API Key", value=os.getenv("TAVILY_API_KEY", ""), key="tavily_api_key", type="password")
    st.text_input("OpenRouter API Key", value=os.getenv("OPENROUTER_API_KEY", ""), key="openrouter_api_key", type="password")
    with st.expander("Langsmith Settings"):
        st.text_input("Langsmith API Key", value=os.getenv("LANGSMITH_API_KEY", ""), key="langsmith_api_key", type="password")
        st.text_input("Langsmith Endpoint", value=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"), key="langsmith_endpoint")
        st.text_input("Langsmith Project", value=os.getenv("LANGSMITH_PROJECT", "blog-post-generator-workflow"), key="langsmith_project")
        st.checkbox("Langsmith Tracing", value=os.getenv("LANGSMITH_TRACING", "true").lower() == "true", key="langsmith_tracing")
    st.markdown("---")
    st.subheader("ℹ️ About")
    st.markdown(
        """
        - Enter a **topic** and **tone**.
        - Click **Generate Blog Post**.
        - The workflow will generate a strategy, draft, SEO report, and final post.
        """
    )

# --- Main Content ---
st.title("📝 Agentic Blog Post Generator")

st.markdown(
    """
    > This application leverages a sophisticated multi-agent system to automate the research and writing process for you.
    > By inputting a simple topic, the agents will perform comprehensive research, analyze findings, and generate a polished, ready-to-publish blog post.
    """
)

# --- Input Fields ---
topic_input = st.text_input(
    "📖 **Enter Your Blog Post Topic:**",
    value=st.session_state.topic,
    placeholder="e.g., The future of AI in content creation",
)
tone_input = st.text_input(
    "🎭 **Enter the Desired Tone:**",
    value=st.session_state.tone,
    placeholder="e.g., Informative and engaging",
)

with st.container():
    st.subheader("🔥 Or, try one of these suggested topics:")
    suggested_topics = [
        "The future of AI in content creation",
        "The impact of remote work on team collaboration",
        "A beginner's guide to investing in cryptocurrency",
    ]
    cols = st.columns(len(suggested_topics))
    for i, topic in enumerate(suggested_topics):
        with cols[i]:
            if st.button(topic, use_container_width=True):
                st.session_state.topic = topic
                st.session_state.generate = True
    st.markdown("<br>", unsafe_allow_html=True)

# --- Generation Logic ---
if st.button("Generate Blog Post", key="generate_button", help="Click to start the blog post generation process.", type="primary"):
    st.session_state.topic = topic_input
    st.session_state.tone = tone_input
    st.session_state.generate = True

if st.session_state.generate and st.session_state.topic and st.session_state.tone:
    with st.status("Generating your blog post...", expanded=True) as status:
        try:
            status.write("Step 1: Generating Blog Strategy...")
            
            if st.session_state.openai_api_key:
                os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
            if st.session_state.tavily_api_key:
                os.environ["TAVILY_API_KEY"] = st.session_state.tavily_api_key
            if st.session_state.openrouter_api_key:
                os.environ["OPENROUTER_API_KEY"] = st.session_state.openrouter_api_key
            if st.session_state.langsmith_api_key:
                os.environ["LANGSMITH_API_KEY"] = st.session_state.langsmith_api_key
            if st.session_state.langsmith_endpoint:
                os.environ["LANGSMITH_ENDPOINT"] = st.session_state.langsmith_endpoint
            if st.session_state.langsmith_project:
                os.environ["LANGSMITH_PROJECT"] = st.session_state.langsmith_project
            os.environ["LANGSMITH_TRACING"] = str(st.session_state.langsmith_tracing)
            
            result = asyncio.run(workflow.arun(idea=st.session_state.topic, tone=st.session_state.tone))
            
            if result and result.content:
                st.session_state.final_post = result.content
                status.update(label="Blog post generated successfully!", state="complete")
            else:
                st.session_state.final_post = None
                status.update(label="Workflow did not produce any content.", state="error")

        except Exception as e:
            st.session_state.final_post = None
            status.update(label=f"An error occurred: {e}", state="error")
    
    st.session_state.generate = False # Reset the flag

# --- Display Final Post ---
if st.session_state.final_post:
    post = st.session_state.final_post
    st.subheader(post.title)
    st.write(f"**Date:** {post.date}")
    st.write(f"**Tags:** {', '.join(post.tags)}")
    st.markdown("---")
    st.markdown(post.draft)

    # --- Download Button ---
    st.download_button(
        label="⬇️ Download Blog Post",
        data=f"# {post.title}\n\n**Date:** {post.date}\n**Tags:** {', '.join(post.tags)}\n\n---\n\n{post.draft}",
        file_name=f"{post.title.lower().replace(' ', '_')}.md",
        mime="text/markdown",
    )