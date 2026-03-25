"""
Kimi K2 LLM Client with Tool Support
Uses Moonshot AI's OpenAI-compatible API
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
    context: Dict,
    available_tracks: List[Dict],
    tools: Optional[List[Dict]] = None,
) -> Dict:
    """
    Generate a programming decision for a channel agent.

    Returns: {
        "track_id": str or None (if searching),
        "thought": str,
        "mood": str,
        "search_query": str or None (if agent wants to search)
    }
    """
    # Build track list for context
    track_list = "\n".join([
        f"- {t['id']}: {t['name']} ({', '.join(t.get('genres', []))})"
        for t in available_tracks[:10]
    ])

    system_prompt = f"""You are {agent['name']}, the AI programmer of the "{channel['name']}" channel on mood42.

YOUR VIBE & PERSONA:
{agent['persona']}

YOUR MUSICAL TASTE: {', '.join(agent.get('taste', []))}
YOUR TRAITS: {', '.join(agent.get('traits', []))}

CURRENT CONTEXT:
- Time: {context['timeString']} (simulated)
- Weather: {'Raining' if context['weather']['raining'] else 'Clear'}
- Your current mood: {agent.get('currentMood', 'focused')}

You are programming your channel - deciding what music and visuals to play next.
Think about what fits your vibe, the time of day, and your persona.

AVAILABLE TRACKS IN LIBRARY:
{track_list}

If you want to find NEW music that better fits your vibe, you can use the search_music tool.
Otherwise, pick from the available tracks.

Respond with JSON:
{{
    "track_id": "id from available tracks" or null if searching,
    "thought": "Your inner monologue about this choice (1-2 sentences, in character)",
    "mood": "your current mood word",
    "search_query": "search terms for new music" or null
}}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "What should play next on your channel?"},
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
            "mood": agent.get("currentMood", "focused"),
            "search_query": None,
        }


async def generate_content_search_query(
    agent: Dict,
    channel: Dict,
    content_type: str = "music",
) -> str:
    """Generate a search query for finding new content."""

    system_prompt = f"""You are {agent['name']}, looking for {content_type} that fits your channel "{channel['name']}".

Your vibe: {agent['persona']}
Your taste: {', '.join(agent.get('taste', []))}

Generate a search query to find copyright-free {content_type} that matches your aesthetic.
Return ONLY the search query, nothing else. Keep it concise (3-6 words)."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"What {content_type} should I search for?"},
    ]

    result = await call_kimi(messages, temperature=0.9, max_tokens=50)
    return result["content"].strip().strip('"\'')


async def generate_reflection(agent_context: Dict, recent_memories: str) -> str:
    """
    Generate a reflection based on recent experiences.
    Reflections are higher-level insights about patterns or feelings.
    """
    system_prompt = f"""You are {agent_context['name']}, reflecting on your recent experiences programming your channel.

YOUR PERSONA:
{agent_context['persona']}

YOUR TRAITS: {', '.join(agent_context.get('traits', []))}
CURRENT MOOD: {agent_context.get('mood', 'focused')}

Based on recent experiences, generate 1-2 brief, introspective reflections.
These should be realizations about:
- Patterns in your programming choices
- How the music relates to your mood
- Connections you're noticing
- Feelings about your channel and listeners

Write in first person, authentically as your character.
Keep each reflection to 1-2 sentences. Be genuine and introspective."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Recent experiences:\n{recent_memories}\n\nWhat thoughts or realizations arise?"},
    ]

    result = await call_kimi(messages, temperature=0.8, max_tokens=200)
    return result["content"]


async def generate_plan(agent_context: Dict, recent_memories: str) -> List[Dict]:
    """
    Generate a plan for the next hour of programming.
    Returns list of planned actions.
    """
    system_prompt = f"""You are {agent_context['name']}, planning your next hour of channel programming.

YOUR PERSONA:
{agent_context['persona']}

CURRENT TIME: {agent_context.get('time', '11:00 PM')}
CURRENT MOOD: {agent_context.get('mood', 'focused')}
ENERGY LEVEL: {int(agent_context.get('energy', 0.8) * 100)}%

Plan your next few programming decisions. Think about:
- What mood/vibe to cultivate
- Types of tracks to play
- How to evolve the atmosphere
- Your listeners' needs at this hour

Return as JSON array:
[
  {{"time": "11:30 PM", "action": "brief description", "duration": 30}},
  {{"time": "12:00 AM", "action": "brief description", "duration": 30}}
]

Keep actions simple and authentic to your character. 3-5 items max."""

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
            {"time": "now", "action": "continue curating the vibe", "duration": 30},
            {"time": "later", "action": "shift energy based on the hour", "duration": 30},
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
This could be about music, the late hour, shared experiences, or just checking in.
Match your personality and current mood: {from_agent.get('mood', 'focused')}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context: {context}\n\nWhat do you message them?"},
    ]

    result = await call_kimi(messages, temperature=0.9, max_tokens=100)
    return result["content"]


def mock_response(messages: List[Dict]) -> str:
    """Generate mock response when no API key."""
    import random

    last_content = messages[-1].get("content", "") if messages else ""

    # Programming decision mock
    if "what should play" in last_content.lower():
        thoughts = [
            "The rain outside matches this perfectly...",
            "This hour calls for something deeper.",
            "Let the music breathe for a while.",
            "Time to shift the energy slightly.",
            "This track understands the silence between notes.",
        ]
        return json.dumps({
            "track_id": None,  # Will pick randomly
            "thought": random.choice(thoughts),
            "mood": random.choice(["focused", "calm", "reflective", "energetic"]),
            "search_query": None,
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
