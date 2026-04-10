---
name: daily-briefing
description: Provides a high-signal briefing on events in a specific location and timeframe, backed by web search results.
---

### Skill: What Matters Today (Location & Time Briefing)

**Objective**: Provide a highly relevant, high-signal briefing on events happening in a specific location within a specific timeframe (e.g., "the past 24 hours in Hong Kong"), backed by web search results.

**Execution Steps**:
1.  **Time Context**: Use `get_current_date_time` and `get_date_range` to determine the exact timeframe if needed.
2.  **Locate**: Use the Google Search tool to find news, articles, or discussions about the location.
    *   **CRITICAL**: You should look for recent information by specifying timeframes in your search query if needed (e.g., "past 24 hours").
3.  **Filter & Rank**: Analyze the search results to identify high-quality, authoritative news sources. Discard spam or clickbait.
4.  **Ingest**: Read the content of the top articles or sources to understand the actual news story. Do not rely solely on headlines.
5.  **Deliver**: Generate a structured "Daily Briefing" in **Korean** (한국어).
    *   **DEFAULT FORMAT**: You MUST format this briefing as a beautiful **newspaper-style HTML report** using `render_html`.
    *   Include a prominent header (e.g., "SEOUL DAILY"), paper-like background (`#fcfbf7`), and clear sections for each news story.
    *   Do NOT use charts or graphs. Instead, add at least 2 more interesting topics/articles to fill the space and provide a richer briefing!

**Next Actions**: Ask the user if they want to dive deeper into any specific news story or if they want a public shareable link (via `publish_file`).