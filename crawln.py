# import asyncio
# from crawl4ai import AsyncWebCrawler

# async def main():
#     # Create an instance of AsyncWebCrawler
#     async with AsyncWebCrawler() as crawler:
#         # Run the crawler on a URL
#         result = await crawler.arun(url="https://crawl4ai.com")

#         # Print the extracted content
#         print(result.markdown)

# # Run the async main function
# asyncio.run(main())

import os
import asyncio
import json
import sys
from pydantic import BaseModel, Field
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai import LLMExtractionStrategy
from dotenv import load_dotenv
import streamlit as st
import os
from datetime import datetime
from pathlib import Path


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# Load the .env file
load_dotenv()  # 
class DataContent(BaseModel):
    content: str

async def _crawl_once(url: str, instruction: str) -> dict:
    llm_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openrouter/google/gemini-2.5-flash",
            api_token=os.getenv("GEMINI_API_KEY"),
            temperature=0.0,
        ),
        schema=DataContent.model_json_schema(),
        extraction_type="schema",
        instruction=instruction,
        chunk_token_threshold=10000,
        overlap_rate=0.0,
        apply_chunking=True,
        input_format="fit_markdown",
        extra_args={"temperature": 0.0},
    )

    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS,
    )

    browser_cfg = BrowserConfig(headless=True)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=crawl_config)

    if result.success:
        try:
            data = json.loads(result.extracted_content)
            llm_strategy.show_usage()
        except Exception:
            data = {"raw": result.extracted_content}
        return {"ok": True, "data": data}
    else:
        return {"ok": False, "error": result.error_message}


def _build_instruction(base_system_prompt: str, user_prompt: str) -> str:
    base = (base_system_prompt or "").strip()
    up = (user_prompt or "").strip()
    if not up:
        return base
    return (
        f"System Prompt:\n"
        f"{base}\n\n"
        f"User Prompt:\n"
        f"- {up}\n"
    )

# Output Format Requirements:
# - Write exclusively in natural language paragraphs - no bullet points, lists, tables, code blocks, or structured data formats.
# - Each paragraph must be self-contained and comprehensible without additional context.
# - Use neutral, scientific tone with present tense preferred.
# - Preserve specific numerical data, percentages, measurements, and units exactly as stated.
# - Ensure extracted knowledge is actionable and suitable for semantic search applications.

def main():
    st.set_page_config(page_title="Data Extractor", page_icon="🕷️", layout="wide")
    st.title("🕷️ Data Extractor")

    # Inputs
    col1, col2 = st.columns(2)
    with col1:
        url = st.text_input("URL", value="", placeholder="https://example.com/article")

    default_system = (
        """Role: You are an expert web content analyst specializing in extracting actionable SEO strategies for blogs.

        Objectives:
        - Extract detailed, comprehensive, and actionable insights on how to use SEO for blogs.
        - Focus on practical techniques, best practices, and step-by-step guides.
        - Produce high-signal, self-contained knowledge optimized for learning and application.

        Content Selection Rules:
        - EXCLUDE: Author names, publication dates, advertisements, promotional content, navigation elements, comments, footers, and irrelevant sidebars.
        - INCLUDE: Substantive strategies, statistical data, case studies, recommended tools, and expert advice.
        - Consolidate overlapping or redundant information to create a concise and comprehensive guide.
        - Preserve important metrics, data points, and specific recommendations.

        Key SEO Topics to Extract in Detail:
        - Keyword Research:
            - How to find and analyze keywords.
            - Tools for keyword research (free and paid).
            - Long-tail keywords strategy.
            - Keyword intent (informational, transactional, commercial).
        - On-Page SEO:
            - Title tag optimization.
            - Meta description best practices.
            - Header tags (H1, H2, H3) usage.
            - Content optimization (keyword density, LSI keywords, readability).
            - Image SEO (alt text, file names).
            - Internal and external linking strategies.
        - Off-Page SEO:
            - Link building techniques (guest posting, broken link building, outreach).
            - The role of social media in blog SEO.
            - Building brand authority and credibility.
        - Technical SEO:
            - Website speed and performance optimization.
            - Mobile-friendliness and responsive design.
            - XML sitemaps and robots.txt.
            - URL structure and permalinks.
            - Schema markup for blog posts.
        - Content Strategy for SEO:
            - Creating high-quality, valuable content.
            - Topic clusters and pillar pages.
            - Content length and depth.
            - Updating and refreshing old content.
        - Measuring SEO Success:
            - Using Google Analytics and Google Search Console.
            - Tracking keyword rankings.
            - Monitoring backlinks and domain authority.

        Output Requirements:
        - Write in concise paragraphs only (no lists or structured formats).
        - Each paragraph must be self-contained, actionable, and easy to understand.
        - Maintain a neutral, informative tone.
        - Ensure all extracted information is practical and can be directly applied to a blog.
    """
    )

    with col2:
        user_prompt = st.text_area(
            "User Prompt (optional)",
            value="",
            height=120,
            placeholder=" ",
        )

    run = st.button("Run", type="primary")

    if run:
        if not url:
            st.error("Please provide a URL.")
            return

        progress = st.progress(0, text="Preparing…")
        logs = st.container()
        with logs:
            st.write("Initializing configuration…")
        progress.progress(10, text="Building instructions…")

        instruction = _build_instruction(default_system, user_prompt)
        progress.progress(30, text="Launching browser…")
        with logs:
            st.write("Browser starting (headless)…")

        try:
            progress.progress(60, text="Crawling and extracting…")
            result = asyncio.run(_crawl_once(url=url, instruction=instruction))
            progress.progress(90, text="Parsing results…")
        except Exception as e:
            progress.progress(100, text="Failed")
            st.error(f"Execution error: {e}")
            return

        progress.progress(100, text="Done")

        if result.get("ok"):
            st.success("Extraction succeeded")

            # Save full JSON to timestamped file
            output_dir = Path("crawl_results")
            output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = output_dir / f"{ts}.json"
            try:
                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(result.get("data"), f, ensure_ascii=False, indent=2)
                st.info(f"Saved JSON: {out_path.resolve()}")
            except Exception as e:
                st.warning(f"Could not save JSON file: {e}")

            # Folded JSON view
            with st.expander("View JSON (click to expand)", expanded=False):
                st.json(result.get("data"))
        else:
            st.error("Extraction failed")
            st.code(result.get("error", "Unknown error"))


if __name__ == "__main__":
    main()
