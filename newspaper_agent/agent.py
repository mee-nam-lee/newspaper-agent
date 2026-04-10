import os
import pathlib

from google import genai
from google.adk.agents import Agent
from google.adk.skills import load_skill_from_dir
from google.adk.tools import load_artifacts
from google.adk.tools.skill_toolset import SkillToolset

from .common.llm import GeminiWithLocation
from .common.utils import load_prompt
from .config import config
from .tools import (
    search_google,
    get_current_date_time,
    get_date_range,
    publish_file,
    render_html
)


# ---------------------------------------------------------------------------
# ADK Skills: Modular, progressive disclosure workflows
# ---------------------------------------------------------------------------
skills_root = pathlib.Path(__file__).parent / "skills"

skills = [
    load_skill_from_dir(skills_root / name)
    for name in [
        "daily-briefing",
    ]
]

skill_toolset = SkillToolset(skills=skills)

newspaper_agent = Agent(
    model=GeminiWithLocation(
        model=config.agent_settings.model, location=config.GOOGLE_GENAI_LOCATION
    ),
    name="newspaper_agent",
    description="Agent for generating premium newspapers",
    instruction=load_prompt(os.path.dirname(__file__), "newspaper_agent.txt"),
    sub_agents=[],
    tools=[
        search_google,
        get_current_date_time,
        get_date_range,
        render_html,
        publish_file,
        skill_toolset,  # Registers list_skills, load_skill, load_skill_resource
        load_artifacts,
    ],
    generate_content_config=genai.types.GenerateContentConfig(
        max_output_tokens=config.YOUTUBE_AGENT_MAX_OUTPUT_TOKENS,
    ),
)

root_agent = newspaper_agent
