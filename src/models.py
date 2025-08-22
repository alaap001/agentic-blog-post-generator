from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()

class BlogStrategy(BaseModel):
    """
    A comprehensive strategy for a blog post, including a title, subtopics, and keywords.
    """

    title: str = Field(..., description="A compelling title for the blog post.")
    subtopics: List[str] = Field(
        ...,
        description="A list of 5-7 detailed and logically flowing subtopics that form the structure of the blog post.",
    )
    keywords: List[str] = Field(
        ...,
        description="A list of 10-15 relevant SEO keywords, including a mix of short-tail and long-tail terms.",
    )


class ResearchReport(BaseModel):
    """
    A research report containing summaries of competitor content and key findings.
    """

    summaries: List[str] = Field(
        ..., description="A list of summaries of competitor blog posts or articles."
    )
    key_findings: List[str] = Field(
        ..., description="A list of key findings and insights from the research."
    )


class BlogOutline(BaseModel):
    """
    A detailed, SEO-optimized outline for a blog post.
    """

    outline: List[str] = Field(
        ...,
        description="A list of headings and subheadings that structure the blog post.",
    )


class BlogDraft(BaseModel):
    """
    A complete draft of a blog post.
    """

    draft: str = Field(..., description="The full text of the blog post draft.")


class SEOReport(BaseModel):
    """
    A report card for SEO analysis, including suggestions for improvement.
    """

    seo_score: float = Field(..., description="An overall SEO score from 0 to 100.")
    suggestions: List[str] = Field(
        ..., description="A list of actionable suggestions for improving SEO."
    )


class EditedDraft(BaseModel):
    """
    An edited version of the blog post draft.
    """

    edited_draft: str = Field(
        ..., description="The edited and improved version of the blog post draft."
    )


class FactCheckReport(BaseModel):
    """
    A report of fact-checked claims from the blog post.
    """

    verified_claims: List[str] = Field(
        ..., description="A list of claims that have been verified as accurate."
    )
    disputed_claims: List[str] = Field(
        ..., description="A list of claims that could not be verified or are inaccurate."
    )


class FinalBlogPost(BaseModel):
    """
    The final, structured blog post output.
    """

    title: str = Field(..., description="Title for the blog post.")
    date: str = Field(..., description="Today's date in YYYY-MM-DD format.")
    tags: List[str] = Field(
        ..., description="A list of relevant SEO tags for the blog post."
    )
    draft: str = Field(
        ..., description="The complete draft of the blog post in markdown format."
    )