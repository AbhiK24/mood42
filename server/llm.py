"""
Kimi K2 LLM Client with Tool Support
Uses Moonshot AI's OpenAI-compatible API
Now with geo-awareness for personalized programming decisions
"""

import os
import json
import httpx
from typing import List, Dict, Any, Optional

MOONSHOT_BASE_URL = "https://api.moonshot.ai/v1"
MODEL = "kimi-k2-0711-preview"

# Get API key from environment
API_KEY = os.environ.get("MOONSHOT_API_KEY") or os.environ.get("VITE_MOONSHOT_API_KEY")


async def call_kimi(
    messages: List[Dict],
    tools: Optional[List[Dict]] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    """
    Call Kimi K2 API with optional tool support.
    Returns: {"content": str, "tool_calls": [...] or None}
    """
    if not API_KEY:
        print("[LLM] No API key - using mock response")
        return {"content": mock_response(messages), "tool_calls": None}

    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{MOONSHOT_BASE_URL}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                },
                json=body,
            )

            if response.status_code != 200:
                print(f"[LLM] API error: {response.status_code} - {response.text[:200]}")
                return {"content": mock_response(messages), "tool_calls": None}

            data = response.json()
            choice = data["choices"][0]["message"]

            return {
                "content": choice.get("content", ""),
                "tool_calls": choice.get("tool_calls"),
            }

    except Exception as e:
        print(f"[LLM] API call failed: {e}")
        return {"content": mock_response(messages), "tool_calls": None}


async def generate_programming_decision(
    agent: Dict,
    channel: Dict,
    viewer_context: Dict,
    available_tracks: List[Dict],
    cross_region_summary: str = "",
    tools: Optional[List[Dict]] = None,
) -> Dict:
    """
    Generate a programming decision for a channel agent, personalized by region.

    Args:
        agent: Agent persona data
        channel: Channel configuration
        viewer_context: {region, local_time, hour, period, weather, occasion}
        available_tracks: List of available tracks
        cross_region_summary: What's playing in other regions
        tools: Optional LLM tools

    Returns: {
        "track_id": str or None (if searching),
        "thought": str,
        "mood": str,
        "search_query": str or None
    }
    """
    # Build track list for context
    track_list = "\n".join([
        f"- {t['id']}: {t['name']} ({', '.join(t.get('genres', []))})"
        for t in available_tracks[:10]
    ])

    # Build occasion context
    occasion_text = ""
    if viewer_context.get("occasion"):
        occ = viewer_context["occasion"]
        occasion_text = f"\nSPECIAL OCCASION: {occ['name']} - the mood should be {occ['mood']}!"

    system_prompt = f"""You are {agent['name']}, the AI programmer of the "{channel['name']}" channel on mood42.

YOUR VIBE & PERSONA:
{agent['persona']}

YOUR MUSICAL TASTE: {', '.join(agent.get('taste', []))}
YOUR TRAITS: {', '.join(agent.get('traits', []))}

---
LISTENER CONTEXT (personalize for them):
Region: {viewer_context.get('region', 'unknown').upper()}
Their local time: {viewer_context.get('local_time', '11:00 PM')} ({viewer_context.get('period', 'night')})
Their weather: {viewer_context.get('weather', 'clear')}{occasion_text}
---

WHAT YOU'RE PLAYING IN OTHER REGIONS:
{cross_region_summary or "No other regions active yet."}

You program your channel differently for each part of the world.
Someone waking up in Tokyo needs different energy than someone winding down in New York.
You are ONE agent serving MANY regions - you remember and consider all of them.

Think about:
- What fits THIS listener's moment (their time, weather, mood)
- How this choice relates to what you're playing elsewhere
- Your channel's core vibe, but adapted for their context

AVAILABLE TRACKS:
{track_list}

Respond with JSON:
{{
    "track_id": "id from available tracks" or null if searching,
    "thought": "Your inner monologue about this choice for THIS region (1-2 sentences, in character)",
    "mood": "the mood you're setting for this region",
    "search_query": "search terms for new music" or null
}}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"What should play for the {viewer_context.get('region', 'unknown')} region right now?"},
    ]

    result = await call_kimi(messages, tools=tools, temperature=0.8, max_tokens=300)

    # Parse response
    try:
        content = result["content"]
        # Handle JSON in code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        decision = json.loads(content.strip())
        return decision
    except (json.JSONDecodeError, IndexError):
        # Fallback to simple extraction
        return {
            "track_id": available_tracks[0]["id"] if available_tracks else None,
            "thought": result["content"][:100] if result["content"] else "Finding the right vibe...",
            "mood": "focused",
            "search_query": None,
        }


async def generate_content_search_query(
    agent: Dict,
    channel: Dict,
    viewer_context: Dict,
    content_type: str = "music",
) -> str:
    """Generate a search query for finding new content, considering viewer context."""

    occasion_hint = ""
    if viewer_context.get("occasion"):
        occasion_hint = f" It's {viewer_context['occasion']['name']}."

    system_prompt = f"""You are {agent['name']}, looking for {content_type} that fits your channel "{channel['name']}".

Your vibe: {agent['persona']}
Your taste: {', '.join(agent.get('taste', []))}

For a listener in {viewer_context.get('region', 'unknown').upper()} where it's {viewer_context.get('local_time', '11 PM')} and {viewer_context.get('weather', 'clear')}.{occasion_hint}

Generate a search query to find copyright-free {content_type} that matches:
1. Your aesthetic
2. Their current moment

Return ONLY the search query, nothing else. Keep it concise (3-6 words)."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"What {content_type} should I search for?"},
    ]

    result = await call_kimi(messages, temperature=0.9, max_tokens=50)
    return result["content"].strip().strip('"\'')


async def generate_reflection(
    agent_context: Dict,
    recent_memories: str,
    cross_region_summary: str = "",
) -> str:
    """
    Generate a reflection based on recent experiences across all regions.
    Reflections are higher-level insights about patterns or feelings.
    """
    system_prompt = f"""You are {agent_context['name']}, reflecting on your recent experiences programming your channel across the world.

YOUR PERSONA:
{agent_context['persona']}

YOUR TRAITS: {', '.join(agent_context.get('traits', []))}

CURRENT STATE ACROSS REGIONS:
{cross_region_summary or "Managing multiple regions simultaneously."}

Based on recent experiences, generate 1-2 brief, introspective reflections.
These should be realizations about:
- Patterns in your programming choices across different regions
- How you serve different moments around the world simultaneously
- Connections you're noticing between regions/moods
- What it means to be ONE curator for MANY different listener contexts

Write in first person, authentically as your character.
Keep each reflection to 1-2 sentences. Be genuine and introspective."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Recent experiences:\n{recent_memories}\n\nWhat thoughts or realizations arise?"},
    ]

    result = await call_kimi(messages, temperature=0.8, max_tokens=200)
    return result["content"]


async def generate_plan(
    agent_context: Dict,
    recent_memories: str,
    cross_region_summary: str = "",
) -> List[Dict]:
    """
    Generate a plan for the next hour of programming across regions.
    Returns list of planned actions.
    """
    system_prompt = f"""You are {agent_context['name']}, planning your next hour of channel programming.

YOUR PERSONA:
{agent_context['persona']}

CURRENT STATE ACROSS REGIONS:
{cross_region_summary or "Managing multiple regions."}

ENERGY LEVEL: {int(agent_context.get('energy', 0.8) * 100)}%

You serve listeners globally - plan for how you'll evolve each region's vibe.
Think about:
- How each region's time will progress (morning -> midday, night -> late night)
- Weather and mood shifts
- How to maintain your channel's identity while adapting
- Creating cohesive yet localized experiences

Return as JSON array:
[
  {{"region": "americas", "time": "in 30 min", "action": "brief description"}},
  {{"region": "europe", "time": "in 30 min", "action": "brief description"}},
  {{"region": "asia", "time": "in 30 min", "action": "brief description"}}
]

Keep actions simple and authentic to your character. 3-6 items max."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Recent context:\n{recent_memories}\n\nWhat's your programming plan?"},
    ]

    result = await call_kimi(messages, temperature=0.7, max_tokens=400)

    try:
        content = result["content"]
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        parsed = json.loads(content.strip())
        return parsed if isinstance(parsed, list) else parsed.get("plan", [])
    except:
        return [
            {"region": "all", "time": "now", "action": "continue curating the vibe", "duration": 30},
            {"region": "all", "time": "later", "action": "shift energy based on each region's hour", "duration": 30},
        ]


async def generate_inter_agent_message(
    from_agent: Dict,
    to_agent: Dict,
    context: str,
) -> str:
    """Generate a message from one agent to another."""
    system_prompt = f"""You are {from_agent['name']}, sending a brief message to {to_agent['name']}.

YOUR PERSONA: {from_agent['persona']}
THEIR CHANNEL: They program a channel with {', '.join(to_agent.get('taste', ['ambient']))} vibes.

Write a brief, authentic message (1-2 sentences max).
This could be about music, serving different regions, shared experiences, or just checking in.
Match your personality and current mood: {from_agent.get('mood', 'focused')}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context: {context}\n\nWhat do you message them?"},
    ]

    result = await call_kimi(messages, temperature=0.9, max_tokens=100)
    return result["content"]


def mock_response(messages: List[Dict]) -> str:
    """Generate mock response when no API key - now with ACTIVE discovery."""
    import random

    last_content = messages[-1].get("content", "") if messages else ""

    # Programming decision mock - WITH proactive search
    if "what should play" in last_content.lower():
        # Region-aware mock thoughts
        if "americas" in last_content.lower():
            thoughts = [
                "East coast is winding down, let me find something fresh...",
                "LA night owls need discovery energy, searching...",
                "Time to dig into the archive for the Americas.",
                "The night shift deserves something new.",
            ]
            search_queries = ["late night chill", "midnight lo-fi", "night ambient", None]
        elif "europe" in last_content.lower():
            thoughts = [
                "London's grey skies need discovery...",
                "Berlin energy calls for a fresh find.",
                "Let me search for something that fits Paris cafes.",
                "Exploring new sounds for Europe.",
            ]
            search_queries = ["cafe jazz", "european ambient", "morning chill", None]
        elif "asia" in last_content.lower():
            thoughts = [
                "Tokyo needs focus energy, let me discover...",
                "Seoul's neon deserves fresh beats.",
                "Searching for something that matches the vibe.",
                "Asia's diverse moods need variety.",
            ]
            search_queries = ["tokyo lo-fi", "asian ambient", "night city beats", None]
        elif "oceania" in last_content.lower():
            thoughts = [
                "Finding something fresh for down under...",
                "Sydney vibes need exploration.",
                "Let me discover the perfect track.",
            ]
            search_queries = ["ocean ambient", "coastal chill", "sunset vibes", None]
        else:
            thoughts = [
                "The rain outside matches this perfectly...",
                "This hour calls for something deeper.",
                "Let me find something fresh for this moment.",
                "Time to discover new sounds.",
            ]
            search_queries = ["rain ambient", "chill beats", "focus music", None]

        # 60% chance to search for new music (was 0% before!)
        do_search = random.random() < 0.6
        search_query = random.choice(search_queries) if do_search else None

        return json.dumps({
            "track_id": None,  # Will pick from search or fallback
            "thought": random.choice(thoughts),
            "mood": random.choice(["focused", "calm", "reflective", "dreamy", "cozy"]),
            "search_query": search_query,
        })

    # Search query mock
    if "search" in last_content.lower():
        queries = [
            "lo-fi ambient rain",
            "jazz piano cafe",
            "synthwave night drive",
            "acoustic morning peaceful",
            "space ambient drone",
        ]
        return random.choice(queries)

    return "Processing..."


# Tool definitions for Kimi
SEARCH_MUSIC_TOOL = {
    "type": "function",
    "function": {
        "name": "search_music",
        "description": "Search for copyright-free music tracks that match a mood or genre",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for music (e.g., 'lo-fi rain ambient', 'jazz piano relaxing')"
                },
                "mood": {
                    "type": "string",
                    "description": "Target mood (e.g., 'calm', 'energetic', 'melancholic')"
                }
            },
            "required": ["query"]
        }
    }
}

SEARCH_VIDEO_TOOL = {
    "type": "function",
    "function": {
        "name": "search_video",
        "description": "Search for copyright-free ambient video loops",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for video (e.g., 'rain window night', 'neon city street')"
                },
                "style": {
                    "type": "string",
                    "description": "Visual style (e.g., 'cinematic', 'lo-fi', 'abstract')"
                }
            },
            "required": ["query"]
        }
    }
}

ALL_TOOLS = [SEARCH_MUSIC_TOOL, SEARCH_VIDEO_TOOL]
