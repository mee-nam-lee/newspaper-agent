import datetime
import json
import logging
import math
import os
import random
import re
import string

from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types


from .config import config
from pydantic import BaseModel

logger = logging.getLogger(__name__)


from google import genai

def search_google(query: str) -> str:
    """Searches Google for the given query using Gemini's search grounding.

    Args:
        query: The search term.
    """
    import time
    
    max_retries = 3
    base_delay = 2.0
    
    for attempt in range(max_retries + 1):
        try:
            client = genai.Client()
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                ),
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Received 429 error. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                continue
                
            logger.error(f"Error in search_google: {e}")
            return f"죄송합니다. 구글 검색(Gemini Grounding) 호출 중 오류가 발생했습니다. 이 오류 내용을 바탕으로 사용자에게 검색에 실패했음을 친절하게 안내하고, 검색 없이 가능한 한 기존 지식을 활용하여 부드럽게 답변을 마무리해 주세요. (상세 에러: {e})"






def get_current_date_time():
    """
    Returns the current date and time in UTC (RFC 3339 format).
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_date_range(time_span: str):
    """
    Calculates the date for the start of a time span relative to now.

    Args:
        time_span: The time span to calculate. Options: 'week', 'month', '3month', 'year'.

    Returns:
        A string representing the date in RFC 3339 format (e.g., '2023-01-01T00:00:00Z').
        Returns empty string if time_span is not recognized.
    """
    now = datetime.datetime.now(datetime.timezone.utc)

    if time_span == "week":
        delta = datetime.timedelta(weeks=1)
    elif time_span == "month":
        delta = datetime.timedelta(days=30)
    elif time_span == "3month":
        delta = datetime.timedelta(days=90)
    elif time_span == "year":
        delta = datetime.timedelta(days=365)
    else:
        return ""

    past_date = now - delta
    return past_date.isoformat()


async def render_html(
    html_content: str, filename: str, tool_context: ToolContext
):
    """
    Saves HTML content to a file and optionally registers it as an artifact.

    Args:
        html_content: The raw HTML string.
        filename: The output filename.
        tool_context: The ADK tool context (automatically injected if available).

    Returns:
        The path to the saved file.
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filepath = os.path.join(output_dir, filename)

        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Try to save artifact if context is available
        try:
            await tool_context.save_artifact(
                filename.replace(".", "_"),  # Simple artifact name
                types.Part.from_bytes(
                    data=html_content.encode("utf-8"), mime_type="text/html"
                ),
            )
            logger.info("Successfully saved HTML to tool context")
        except Exception as e:
            logger.warning(f"Warning: Failed to save artifact: {e}")

        return f"HTML saved to {filename}"
    except Exception as e:
        return f"Error saving HTML: {e!s}"


def parse_timestamp_to_seconds(timestamp_str: str) -> int:
    """
    Parses a timestamp string into an integer representing total seconds.

    Supports formats: raw seconds ('322'), MM:SS ('05:22'), or HH:MM:SS ('1:05:22').

    >>> parse_timestamp_to_seconds('322')
    322
    >>> parse_timestamp_to_seconds('05:22')
    322
    >>> parse_timestamp_to_seconds('5:22')
    322
    >>> parse_timestamp_to_seconds('1:05:22')
    3922
    >>> parse_timestamp_to_seconds('01:05:22')
    3922
    >>> parse_timestamp_to_seconds('invalid')
    0
    """
    try:
        # Match optional HH:, required MM:, required SS
        # Groups: 1=HH (optional), 2=MM (or raw seconds if no colon), 3=SS (optional)
        match = re.fullmatch(
            r"(?:(?:(\d+):)?(\d+):)?(\d+)", str(timestamp_str).strip()
        )
        if not match:
            return 0

        hh, mm, ss = match.groups()

        # If only the last group matched, it's just raw seconds
        if not hh and not mm:
            return int(ss)

        total = 0
        if hh:
            total += int(hh) * 3600
        if mm:
            total += int(mm) * 60
        if ss:
            total += int(ss)

        return total
    except Exception:
        pass
    return 0


# --- NEW METADATA/TEXT TOOLS FOR PR3 ---



def publish_file(
    content: str,
    filename: str,
    mime_type: str = "text/html",
    tool_context: ToolContext = None,
) -> str:
    """
    Publishes content to a temporary public URL using Google Cloud Storage.
    Use this tool when you have generated a comprehensive HTML report or image and need to
    provide the user with a direct link to view it in their browser.

    Args:
        content: The raw string or bytes content to publish.
        filename: The desired filename (e.g., 'report.html' or 'chart.png').
        mime_type: The MIME type of the file (default: 'text/html').
        tool_context: The ADK tool context (automatically injected).

    Returns:
        A string containing the public URL where the user can view the file, or an error message.
    """
    try:
        bucket_name = config.PUBLIC_ARTIFACT_BUCKET
        if not bucket_name:
            return "Error: PUBLIC_ARTIFACT_BUCKET is not set in .env file."

        public_url_prefix = f"https://storage.googleapis.com/{bucket_name}"

        # Determine path parameters
        now = datetime.datetime.now(datetime.timezone.utc)
        date_str = now.strftime("%Y%m%d")

        # Extract session_id if available to group files
        session_folder = "no_session"
        if tool_context and tool_context.session:
            session_folder = tool_context.session.id or "no_session"

        random_str = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )

        # New structure: exports/youtube-analyst/YYYYMMDD/session_id/random/filename
        path_suffix = f"exports/newspaper_agent/{date_str}/{session_folder}/{random_str}/{filename}"

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(path_suffix)

        # Upload the content
        if isinstance(content, str):
            blob.upload_from_string(content, content_type=mime_type)
        else:
            blob.upload_from_string(
                content, content_type=mime_type
            )  # works for bytes too

        logger.info(f"Successfully published file to {path_suffix}")

        return f"File successfully published. View it here: {public_url_prefix}/{path_suffix}"

    except Exception as e:
        logger.error(f"Failed to publish file: {e}")
        return f"Failed to publish file to public URL: {e!s}"
