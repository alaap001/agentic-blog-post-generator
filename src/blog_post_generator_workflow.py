import asyncio
import os
import yaml
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from agno.workflow.v2.workflow import Workflow
from dotenv import load_dotenv
from agno.storage.sqlite import SqliteStorage
from typing import Optional, Any

from .models import BlogStrategy, FinalBlogPost, SEOReport, BlogDraft
from .agents import (
    content_team,
    editor_fact_checker_team,
    seo_optimizer,
    topic_strategist,
)

# Load environment variables from .env file
load_dotenv()

# Set the endpoint and headers for LangSmith
endpoint = f'{os.getenv("LANGSMITH_ENDPOINT")}/otel/v1/traces'
headers = {
    "x-api-key": os.getenv("LANGSMITH_API_KEY"),
    "Langsmith-Project": os.getenv("LANGSMITH_PROJECT"),
}

# Configure the tracer provider
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers))
)
trace_api.set_tracer_provider(tracer_provider=tracer_provider)

AgnoInstrumentor().instrument()


# --- Caching Helper Functions ---
def get_cached_data(workflow: Workflow, key: str, topic: str) -> Optional[Any]:
    """Gets cached data from the workflow session state for a specific topic."""
    return workflow.workflow_session_state.get(key, {}).get(topic)

def set_cached_data(workflow: Workflow, key: str, topic: str, data: Any):
    """Sets data in the workflow session state for a specific topic."""
    if key not in workflow.workflow_session_state:
        workflow.workflow_session_state[key] = {}
    workflow.workflow_session_state[key][topic] = data.model_dump() if hasattr(data, 'model_dump') else data

# --- Main Execution Function ---
async def blog_post_generation_workflow(
    workflow: Workflow,
    idea: str,
    tone: str,
) -> FinalBlogPost:
    """
    Orchestrates the entire blog post generation process from idea to final draft.
    """
    print("--- Starting Blog Post Generation Workflow ---")

    # Check for fully cached final blog post first
    cached_final_post = get_cached_data(workflow, "final_post", idea)
    if cached_final_post:
        print("Found cached final blog post. Returning it.")
        return FinalBlogPost.model_validate(cached_final_post)

    # 1. Generate Strategy
    print("\nStep 1: Generating Blog Strategy...")
    strategy = get_cached_data(workflow, "strategy", idea)
    if strategy:
        strategy = BlogStrategy.model_validate(strategy)
        print("   - Found cached strategy.")
    else:
        print("Cache Not Found Blog Strategy")
        strategy_prompt = f"Generate a blog post strategy for the idea '{idea}' with a '{tone}' tone."
        strategy_response = await topic_strategist.arun(strategy_prompt)
        if not strategy_response or not strategy_response.content:
            raise ValueError("Failed to generate a blog strategy.")
        strategy = strategy_response.content
        set_cached_data(workflow, "strategy", idea, strategy)
        print(f"   - Strategy Title: {strategy.title}")

    # 2. Create First Draft
    print("\nStep 2: Creating First Draft...")
    first_draft = get_cached_data(workflow, "first_draft", idea)
    if first_draft:
        first_draft = BlogDraft.model_validate(first_draft)
        print("   - Found cached first draft.")
    else:
        print("Cache Not Found First Draft")
        content_prompt = f"""
        Blog Post Title: {strategy.title}
        Subtopics: {', '.join(strategy.subtopics)}
        Keywords: {', '.join(strategy.keywords)}

        Please generate the first draft of the blog post.
        """
        draft_response = await content_team.arun(content_prompt)
        if not draft_response or not draft_response.content:
            raise ValueError("Failed to create the first draft.")
        first_draft = draft_response.content
        set_cached_data(workflow, "first_draft", idea, first_draft)
        print("   - First draft created successfully.")

    # 3. SEO Optimization
    print("\nStep 3: Optimizing for SEO...")
    seo_report = get_cached_data(workflow, "seo_report", idea)
    if seo_report:
        seo_report = SEOReport.model_validate(seo_report)
        print("   - Found cached SEO report.")
    else:
        print("Cache Not Found SEO Report")
        seo_prompt = f"Analyze the following blog post draft for SEO and provide suggestions:\n\n{first_draft.draft}"
        seo_response = await seo_optimizer.arun(seo_prompt)
        if not seo_response or not seo_response.content:
            raise ValueError("Failed to get SEO suggestions.")
        seo_report = seo_response.content
        set_cached_data(workflow, "seo_report", idea, seo_report)
    print(f"   - SEO Score: {seo_report.seo_score}")

    # 4. Editing and Fact-Checking
    print("\nStep 4: Editing and Fact-Checking...")
    final_post = get_cached_data(workflow, "final_post", idea)
    if final_post:
        final_post = FinalBlogPost.model_validate(final_post)
        print("   - Found cached final post.")
    else:
        print("Cache Not Found Final Post")
        editing_prompt = f"""
        Please edit and fact-check the following blog post draft.
        Also, consider these SEO suggestions: {seo_report.suggestions}

        Draft:
        {first_draft.draft}
        """
        final_response = await editor_fact_checker_team.arun(editing_prompt)
        if not final_response or not final_response.content:
            raise ValueError("Failed to edit and fact-check the draft.")
        final_post = final_response.content
        set_cached_data(workflow, "final_post", idea, final_post)
        print("   - Final blog post is ready!")

    print("\n--- Workflow Finished ---")
    return final_post


# --- Workflow Definition ---
# Load configuration from YAML file
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

storage_config = config.get("storage", {})

workflow = Workflow(
    name="Blog Post Generator",
    description="A workflow to generate a blog post from a user's idea.",
    steps=blog_post_generation_workflow,
    storage=SqliteStorage(
        table_name=storage_config.get("table_name", "blog_post_generator_cache"),
        db_file=storage_config.get("db_file", "tmp/blog_post_generator.db"),
        mode="workflow_v2",
    ),
    workflow_session_state={}, 
)

if __name__ == "__main__":
    idea = "The future of AI in content creation"
    tone = "Informative and engaging"

    async def main():
        result = await workflow.arun(idea=idea, tone=tone)
        print("\n--- Final Blog Post Output ---")
        if result and result.content:
            final_post = result.content
            print(f"Title: {final_post.title}")
            print(f"Date: {final_post.date}")
            print(f"Tags: {', '.join(final_post.tags)}")
            print("\n--- Draft ---")
            print(final_post.draft)
        else:
            print("Workflow did not produce any content.")
        print("--------------------------")

    asyncio.run(main())