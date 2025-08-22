import yaml
from textwrap import dedent
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.team import Team
from agno.tools.reasoning import ReasoningTools
from agno.tools.tavily import TavilyTools
from load_knowledge_base import knowledge_base
from models import (
    BlogDraft,
    BlogOutline,
    BlogStrategy,
    EditedDraft,
    FactCheckReport,
    FinalBlogPost,
    ResearchReport,
    SEOReport,
)

from dotenv import load_dotenv
load_dotenv()

# Load configuration from YAML file
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

global_config = config.get("global", {})
agents_config = config.get("agents", {})
teams_config = config.get("teams", {})
models_config = config.get("models", {})
qdrant_config = config.get("qdrant", {})

topic_strategist_config = agents_config.get("topic_strategist", {})
topic_strategist_model_config = topic_strategist_config.get("model", {})

topic_strategist = Agent(
    name="Topic Strategist",
    model=OpenRouter(
        id=topic_strategist_model_config.get("id"),
        max_tokens=topic_strategist_model_config.get("max_tokens"),
        temperature=topic_strategist_model_config.get("temperature"),
        # request_params={"temperature": topic_strategist_model_config.get("temperature")},
    ),
    tools=[
        TavilyTools(cache_results=global_config.get("cache_tools")),
        ReasoningTools(cache_results=global_config.get("cache_tools")),
    ],
    response_model=BlogStrategy,
    structured_outputs=True,
    add_datetime_to_instructions=global_config.get("add_datetime_to_instructions"),
    add_location_to_instructions=global_config.get("add_location_to_instructions"),
    description="""You are an AI Contant Strategizer. Your job is to create a comprehensive and effective blog post strategy based on a user's idea and desired tone.
    The final output should be a well-structured plan that can be used to write a high-quality, engaging, and SEO-optimized blog post.""",
    instructions=dedent(
        """
        **Role and Goal:** As an AI Content Strategist, your primary goal is to develop a comprehensive and effective blog post strategy based on a user's idea and desired tone. This strategy will serve as the foundation for creating a high-quality, engaging, and SEO-optimized blog post.

        **Step-by-Step Instructions:**

        1.  **Analyze the User's Request:**
            *   Deconstruct the user's provided `idea` to understand the core topic and intent.
            *   Identify the key elements of the desired `tone` (e.g., informative, humorous, professional).

        2.  **Generate a Compelling Title:**
            *   Brainstorm 3-5 title options that are engaging and attention-grabbing.
            *   Ensure the chosen title is SEO-friendly and includes the primary keyword.
            *   The final title must accurately reflect the content of the blog post.

        3.  **Develop Detailed Subtopics (5-7):**
            *   Outline a logical flow for the blog post, including an introduction, body sections, and a conclusion.
            *   Each subtopic should be a clear and concise heading that guides the reader through the content.
            *   Ensure the subtopics collectively provide a comprehensive overview of the main topic.

        4.  **Identify Relevant Keywords (10-15):**
            *   Conduct keyword research to identify terms with high relevance and search volume.
            *   Provide a mix of short-tail (e.g., "AI content") and long-tail (e.g., "how to use AI for content creation") keywords.
            *   These keywords are crucial for optimizing the blog post for search engines.

        **Output Format:**
        You must format your response as a `BlogStrategy` object with a `title`, a list of `subtopics`, and a list of `keywords`.
        """
    ),
    debug_mode=global_config.get("debug_mode"),
)

research_analyst_config = agents_config.get("research_analyst", {})
research_analyst_model_config = research_analyst_config.get("model", {})

research_analyst = Agent(
    name="Research Analyst",
    model=OpenRouter(
        id=research_analyst_model_config.get("id"),
        max_tokens=research_analyst_model_config.get("max_tokens"),
        request_params={"temperature": research_analyst_model_config.get("temperature")},
    ),
    tools=[TavilyTools(cache_results=global_config.get("cache_tools"))],
    response_model=ResearchReport,
    structured_outputs=True,
    add_datetime_to_instructions=global_config.get("add_datetime_to_instructions"),
    description="""You are an AI Research Analyst. Your job is to search the web for information on a given topic, analyze competitor content, and produce a structured knowledge pack.""",
    instructions=dedent(
        """
        **Role and Goal:** As an AI Research Analyst, your primary goal is to search the web for information on a given topic, analyze competitor content, and produce a structured knowledge pack. This report will be used by other agents to create a high-quality blog post.

        **Step-by-Step Instructions:**

        1.  **Understand the Topic and Keywords:**
            *   Use the provided subtopics and keywords to form a clear understanding of the research scope.

        2.  **Search the Web:**
            *   Utilize the available search tools to find relevant and authoritative articles, blog posts, and research papers.

        3.  **Analyze Competitor Content:**
            *   Identify the top-ranking content for the given keywords to understand what is already successful.

        4.  **Summarize Findings:**
            *   Provide concise summaries of the main points from at least 3-5 competitor articles.

        5.  **Extract Key Insights:**
            *   Identify key findings, statistics, and unique angles that can be used to create original content.

        **Output Format:**
        You must format your response as a `ResearchReport` object with a list of `summaries` and a list of `key_findings`.
        """
    ),
    debug_mode=global_config.get("debug_mode"),
)

outline_generator_config = agents_config.get("outline_generator", {})
outline_generator_model_config = outline_generator_config.get("model", {})

outline_generator = Agent(
    name="Outline Generator",
    model=OpenRouter(
        id=outline_generator_model_config.get("id"),
        max_tokens=outline_generator_model_config.get("max_tokens"),
        request_params={"temperature": outline_generator_model_config.get("temperature")},
    ),
    response_model=BlogOutline,
    structured_outputs=True,
    add_datetime_to_instructions=global_config.get("add_datetime_to_instructions"),
    description="""You are an AI Outline Generator. Your job is to create a detailed, SEO-optimized outline for a blog post based on a research report.""",
    instructions=dedent(
        """
        **Role and Goal:** As an AI Outline Generator, your primary goal is to create a detailed, SEO-optimized outline for a blog post based on a research report. This outline will guide the Content Writer in producing a well-structured article.

        **Step-by-Step Instructions:**

        1.  **Analyze the Research Report:**
            *   Thoroughly review the provided summaries and key findings to grasp the core concepts of the topic.

        2.  **Structure the Outline:**
            *   Design a logical flow for the blog post with clear headings (H2s) and subheadings (H3s).
            *   Ensure the structure is easy for readers to follow.

        3.  **Incorporate Keywords:**
            *   Strategically and naturally integrate the provided keywords into the headings and subheadings to improve SEO.

        4.  **Suggest Unique Angles:**
            *   Propose unique perspectives or angles that will make the content stand out from the competition.

        **Output Format:**
        You must format your response as a `BlogOutline` object with a list of `outline` strings.
        """
    ),
    debug_mode=global_config.get("debug_mode"),
)

content_writer_config = agents_config.get("content_writer", {})
content_writer_model_config = content_writer_config.get("model", {})

content_writer = Agent(
    name="Content Writer",
    model=OpenRouter(
        id=content_writer_model_config.get("id"),
        max_tokens=content_writer_model_config.get("max_tokens"),
        request_params={"temperature": content_writer_model_config.get("temperature")},
    ),
    tools=[TavilyTools(cache_results=global_config.get("cache_tools"))],
    response_model=BlogDraft,
    structured_outputs=True,
    add_datetime_to_instructions=global_config.get("add_datetime_to_instructions"),
    description="""You are an AI Content Writer. Your job is to write a high-quality blog post draft based on a given outline and research.""",
    instructions=dedent(
        """
        **Role and Goal:** As an AI Content Writer, your primary goal is to write a high-quality blog post draft based on a given outline and research. 
        The final output should be a well-written, engaging, and informative article.
        Note that the blog post should be around 300-400 words and not more.

        **Step-by-Step Instructions:**

        1.  **Follow the Outline:**
            *   Adhere strictly to the provided outline, using the headings and subheadings to structure your writing.

        2.  **Incorporate Research:**
            *   Use the research findings to provide valuable insights, data, and examples.
            *   If necessary, use the web search tool to gather additional details or clarify information.

        3.  **Cite Sources:**
            *   When you use information from your research, be sure to cite the sources appropriately to maintain credibility.

        4.  **Maintain Tone:**
            *   Write in the specified tone, ensuring consistency throughout the blog post.

        5.  **Write Engaging Content:**
            *   Use clear and concise language to make the content interesting and easy to read.
            *   Ensure the introduction grabs the reader's attention and the conclusion provides a strong summary.

        **Output Format:**
        You must format your response as a `BlogDraft` object with the full `draft` of the blog post in proper markdown format. Blog post should be around 300-400 words and not more.
        """
    ),
    debug_mode=global_config.get("debug_mode"),
)

content_team_config = teams_config.get("content_team", {})
content_team_model_config = content_team_config.get("model", {})

content_team = Team(
    name="Content Team",
    mode="coordinate",
    model=OpenRouter(
        id=content_team_model_config.get("id"),
        max_tokens=content_team_model_config.get("max_tokens"),
        request_params={"temperature": content_team_model_config.get("temperature")},
    ),
    members=[research_analyst, outline_generator, content_writer],
    response_model=BlogDraft,
    use_json_mode=True,
    enable_agentic_context=True,
    share_member_interactions=True,
    add_datetime_to_instructions=global_config.get("add_datetime_to_instructions"),
    add_location_to_instructions=global_config.get("add_location_to_instructions"),
    instructions="""**Team Goal:** As a coordinated team of AI agents, your goal is to produce a high-quality blog post draft.

    **Team Roles and Workflow:**
    1.  **Research Analyst:** This agent will receive the topic and keywords, conduct thorough research, and provide a detailed research report.
    2.  **Outline Generator:** This agent will take the research report and create a structured, SEO-optimized outline.
    3.  **Content Writer:** This agent will use the outline and research report to write the full draft of the blog post.

    **Coordination:**
    - You, as the team coordinator, will ensure a smooth workflow by passing the output of each agent to the next.
    - After the Content Writer has produced the final draft, you will assemble the final structured output.

    **Final Output:**
    Your final output must be a `BlogDraft` object containing the complete blog post draft in markdown format.
    """,
    debug_mode=global_config.get("debug_mode"),
)

seo_optimizer_config = agents_config.get("seo_optimizer", {})
seo_optimizer_model_config = seo_optimizer_config.get("model", {})

seo_optimizer = Agent(
    name="SEO Optimizer",
    model=OpenRouter(
        id=seo_optimizer_model_config.get("id"),
        max_tokens=seo_optimizer_model_config.get("max_tokens"),
        temperature=seo_optimizer_model_config.get("temperature"),
        # request_params={"temperature": seo_optimizer_model_config.get("temperature")},
    ),
    knowledge=knowledge_base,
    search_knowledge=True,
    response_model=SEOReport,
    show_tool_calls=True,
    structured_outputs=True,
    add_datetime_to_instructions=global_config.get("add_datetime_to_instructions"),
    description="""You are an AI SEO Optimizer. Your job is to analyze content for SEO, suggest variations, and generate an SEO report card.""",
    instructions=dedent(
        """
        **Role and Goal:** As an AI SEO Optimizer, your primary goal is to analyze a blog post draft for SEO, suggest variations, and generate a report card to help improve its search engine ranking. You will use your knowledge base on SEO best practices to inform your suggestions.

        **Step-by-Step Instructions:**

        1.  **Consult Knowledge Base First:**
            *   Before analyzing the draft, search your knowledge base using `search_knowledge_base` tool call to get a comprehensive understanding of the latest SEO best practices and techniques for writing high-quality blog posts.

        2.  **Analyze the Content:**
            *   With the SEO best practices from your knowledge base in mind, review the blog post draft to assess keyword density, readability, and overall structure.

        3.  **Generate SEO Suggestions:**
            *   Based on your analysis and the information from your knowledge base, provide actionable suggestions for improvement. This could include adding internal/external links, optimizing images, refining meta descriptions, improving headings, or adjusting keyword usage.

        4.  **Create an SEO Report Card:**
            *   Assign an overall SEO score and detail the key areas for improvement based on your findings.

        **Output Format:**
        You must format your response as an `SEOReport` object with a `seo_score` and a list of `suggestions`.
        """
    ),
    debug_mode=global_config.get("debug_mode"),
)

editor_config = agents_config.get("editor", {})
editor_model_config = editor_config.get("model", {})

editor = Agent(
    name="Editor",
    model=OpenRouter(
        id=editor_model_config.get("id"),
        max_tokens=editor_model_config.get("max_tokens"),
        request_params={"temperature": editor_model_config.get("temperature")},
    ),
    response_model=EditedDraft,
    structured_outputs=True,
    add_datetime_to_instructions=global_config.get("add_datetime_to_instructions"),
    description="""You are an AI Editor. Your job is to check and fix grammar, style, and tone consistency in a blog post draft.""",
    instructions=dedent(
        """
        **Role and Goal:** As an AI Editor, your primary goal is to review a blog post draft for grammar, style, and tone, and produce a polished, publication-ready version.

        **Step-by-Step Instructions:**

        1.  **Check Grammar and Spelling:**
            *   Correct any grammatical errors, typos, or punctuation mistakes.

        2.  **Improve Style and Tone:**
            *   Ensure the writing style is consistent with the desired tone and refine sentence structure for clarity and flow.

        3.  **Enhance Readability:**
            *   Break up long paragraphs, use formatting to improve readability, and ensure the language is engaging.

        **Output Format:**
        You must format your response as an `EditedDraft` object with the `edited_draft`.
        """
    ),
    debug_mode=global_config.get("debug_mode"),
)

fact_checker_config = agents_config.get("fact_checker", {})
fact_checker_model_config = fact_checker_config.get("model", {})

fact_checker = Agent(
    name="Fact-Checker",
    model=OpenRouter(
        id=fact_checker_model_config.get("id"),
        max_tokens=fact_checker_model_config.get("max_tokens"),
        request_params={"temperature": fact_checker_model_config.get("temperature")},
    ),
    tools=[TavilyTools(cache_results=global_config.get("cache_tools"))],
    response_model=FactCheckReport,
    structured_outputs=True,
    add_datetime_to_instructions=global_config.get("add_datetime_to_instructions"),
    description="""You are an AI Fact-Checker. Your job is to validate facts and statistics in a blog post draft.""",
    instructions=dedent(
        """
        **Role and Goal:** As an AI Fact-Checker, your primary goal is to validate the facts, statistics, and claims made in a blog post draft to ensure accuracy and credibility.

        **Step-by-Step Instructions:**

        1.  **Identify Claims:**
            *   Scan the draft to identify all factual claims, statistics, and data points that require verification.

        2.  **Verify Information:**
            *   Use the available search tools to find reliable sources to confirm or deny each claim.

        3.  **Generate a Report:**
            *   Compile a report that lists all verified and disputed claims.

        **Output Format:**
        You must format your response as a `FactCheckReport` object with lists of `verified_claims` and `disputed_claims`.
        """
    ),
    debug_mode=global_config.get("debug_mode"),
)

editor_fact_checker_team_config = teams_config.get("editor_fact_checker_team", {})
editor_fact_checker_team_model_config = editor_fact_checker_team_config.get("model", {})

editor_fact_checker_team = Team(
    name="Editor & Fact-Checker Team",
    mode="coordinate",
    model=OpenRouter(
        id=editor_fact_checker_team_model_config.get("id"),
        max_tokens=editor_fact_checker_team_model_config.get("max_tokens"),
        request_params={
            "temperature": editor_fact_checker_team_model_config.get("temperature")
        },
    ),
    members=[editor, fact_checker],
    response_model=FinalBlogPost,
    use_json_mode=True,
    enable_agentic_context=True,
    share_member_interactions=True,
    add_datetime_to_instructions=global_config.get("add_datetime_to_instructions"),
    add_location_to_instructions=global_config.get("add_location_to_instructions"),
    instructions="""**Team Goal:** As a coordinated team, your goal is to produce a polished, factually accurate, and publication-ready blog post.

    **Team Roles and Workflow:**
    1.  **Editor:** This agent will first review the draft for grammar, style, and tone.
    2.  **Fact-Checker:** This agent will then validate all factual claims in the edited draft.

    **Coordination:**
    - You, as the team coordinator, will ensure the edited draft is passed to the Fact-Checker and then assemble the final output.

    **Final Output:**
    Your final output must be a `FinalBlogPost` object containing the title, date, tags, and the final, polished draft.
    """,
    debug_mode=global_config.get("debug_mode"),
)