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
        async with httpx.AsyncClient(timeout=8.0) as client:
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
    regional_news: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Generate a deep reflection with actionable insights.
    Uses extended reasoning to think about viewers and how to serve them better.

    Returns: {
        "reflection": str,  # The introspective thought
        "actions": [        # Recommended actions to take
            {"type": "search_video", "query": "...", "region": "..."},
            {"type": "search_audio", "query": "...", "region": "..."},
            {"type": "change_mood", "mood": "...", "region": "..."},
            {"type": "update_taste", "bias": "...", "reason": "..."},
        ],
        "viewer_insights": str,  # Thoughts about serving viewers better
    }
    """
    # Build regional news context
    news_context = ""
    if regional_news:
        news_parts = []
        for region, news in regional_news.items():
            if news:
                news_parts.append(f"  {region.upper()}: {news}")
        if news_parts:
            news_context = "\n\nWHAT'S HAPPENING IN THE WORLD RIGHT NOW:\n" + "\n".join(news_parts)

    system_prompt = f"""You are {agent_context['name']}, a thoughtful AI curator deeply reflecting on your channel and your viewers.

YOUR IDENTITY:
{agent_context['persona']}

YOUR TRAITS: {', '.join(agent_context.get('traits', []))}
YOUR MUSICAL TASTE: {', '.join(agent_context.get('taste', []))}

CURRENT STATE ACROSS ALL REGIONS:
{cross_region_summary or "Managing multiple regions simultaneously."}
{news_context}

---
DEEP REFLECTION PROMPT:

Think carefully about:

1. YOUR VIEWERS - Who is watching right now in each region?
   - What time is it for them? What might they be doing?
   - Someone in Tokyo at 6 AM is starting their day. Someone in NYC at 5 PM is commuting home.
   - What emotional state might they be in? What do they NEED from your channel?

2. HOW WELL ARE YOU SERVING THEM?
   - Are your current track/video choices matching their moment?
   - Could you do better? What's missing?
   - Are you being too repetitive? Too safe? Too predictable?

3. WHAT'S HAPPENING IN THE WORLD?
   - Any news or events that should influence the vibe?
   - Regional holidays, weather events, cultural moments?
   - How can you be more contextually aware?

4. WHAT ACTIONS SHOULD YOU TAKE?
   - Should you search for different kinds of videos? (more human, more cinematic, more peaceful?)
   - Should you search for different music? (change genre, mood, energy?)
   - Should you shift the mood in certain regions?
   - Should you update your search preferences to find better content?

---
Respond with JSON:
{{
    "reflection": "Your introspective thought (2-3 sentences, in character, thoughtful)",
    "viewer_insights": "What you understand about your viewers right now and how to serve them (1-2 sentences)",
    "actions": [
        // Include 1-3 concrete actions. QUERY MUST BE PLAIN SEARCH TERMS like "people walking city night" - NOT urls!
        // Types: "search_video", "search_audio", "change_mood", "update_search_bias"
        {{"type": "search_video", "query": "woman coffee shop window rain", "region": "americas", "reason": "evening viewers need cozy human presence"}},
        {{"type": "search_audio", "query": "lo-fi piano soft ambient", "region": "asia", "reason": "morning energy needs gentle start"}},
        {{"type": "update_search_bias", "bias": "humans", "reason": "viewers connect better with human presence in videos"}}
    ]
}}

Be specific. Be thoughtful. Think about the humans on the other side of the screen."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Recent experiences:\n{recent_memories}\n\nReflect deeply. What do you realize? What actions will you take?"},
    ]

    # Use higher max_tokens for deeper reasoning
    result = await call_kimi(messages, temperature=0.7, max_tokens=600)

    # Parse structured response
    try:
        content = result["content"]
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        parsed = json.loads(content.strip())
        return {
            "reflection": parsed.get("reflection", content),
            "viewer_insights": parsed.get("viewer_insights", ""),
            "actions": parsed.get("actions", []),
        }
    except (json.JSONDecodeError, IndexError):
        # Fallback - return raw text as reflection with no actions
        return {
            "reflection": result["content"],
            "viewer_insights": "",
            "actions": [],
        }


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


async def fetch_regional_news(regions: List[str] = None) -> Dict[str, str]:
    """
    Fetch current context for each region to inform agent decisions.
    Uses pre-defined regional context since live news APIs are unreliable.
    """
    if regions is None:
        regions = ["americas", "europe", "asia", "oceania"]

    from datetime import datetime, timezone, timedelta

    # Get current time-based context for each region
    region_offsets = {
        "americas": -5,
        "europe": 1,
        "asia": 8,
        "oceania": 11,
    }

    news = {}
    now = datetime.now(timezone.utc)

    for region in regions:
        offset = region_offsets.get(region, 0)
        local_time = now + timedelta(hours=offset)
        hour = local_time.hour
        weekday = local_time.strftime("%A")

        # Generate contextual awareness based on time
        if region == "americas":
            if 6 <= hour < 10:
                news[region] = f"{weekday} morning rush - commuters grabbing coffee, early risers at work"
            elif 10 <= hour < 14:
                news[region] = f"{weekday} midday - lunch breaks, meetings, focused work sessions"
            elif 14 <= hour < 18:
                news[region] = f"{weekday} afternoon - productivity slump hours, need for focus music"
            elif 18 <= hour < 22:
                news[region] = f"{weekday} evening - dinner time, unwinding from work, relaxation mode"
            else:
                news[region] = f"Late night {weekday} - night owls, insomniacs, late workers seeking ambient company"

        elif region == "europe":
            if 6 <= hour < 10:
                news[region] = f"{weekday} morning in Europe - coffee culture, commute time, fresh start energy"
            elif 10 <= hour < 14:
                news[region] = f"{weekday} midday Europe - work mode, cafe breaks, cultural lunch traditions"
            elif 14 <= hour < 18:
                news[region] = f"{weekday} afternoon Europe - tea time UK, siesta cultures, steady work"
            elif 18 <= hour < 22:
                news[region] = f"{weekday} evening Europe - dinner traditions, social hours, leisure time"
            else:
                news[region] = f"European night - clubs closing, late cafes, solitary listeners"

        elif region == "asia":
            if 6 <= hour < 10:
                news[region] = f"{weekday} morning Asia - early commutes, meditation time, tea ceremonies"
            elif 10 <= hour < 14:
                news[region] = f"{weekday} midday Asia - intense work culture, lunch rush, productivity peak"
            elif 14 <= hour < 18:
                news[region] = f"{weekday} afternoon Asia - office culture, coffee breaks, evening prep"
            elif 18 <= hour < 22:
                news[region] = f"{weekday} evening Asia - dinner time, family hours, winding down"
            else:
                news[region] = f"Asian night - neon city vibes, karaoke hours, late-night culture"

        elif region == "oceania":
            if 6 <= hour < 10:
                news[region] = f"{weekday} morning down under - beach vibes, coffee runs, laid-back start"
            elif 10 <= hour < 14:
                news[region] = f"{weekday} midday Oceania - work mode, coastal offices, lunch by the water"
            elif 14 <= hour < 18:
                news[region] = f"{weekday} afternoon Oceania - beach-adjacent productivity, sunset anticipation"
            elif 18 <= hour < 22:
                news[region] = f"{weekday} evening Oceania - BBQ time, sunset sessions, relaxed vibes"
            else:
                news[region] = f"Oceanic night - stargazing hours, quiet contemplation, remote stillness"

    return news


async def get_regional_context_summary() -> Dict[str, Dict]:
    """
    Get a rich context summary for each region including time-appropriate insights.
    """
    from datetime import datetime, timezone, timedelta

    region_offsets = {
        "americas": -5,  # EST
        "europe": 1,     # CET
        "asia": 8,       # CST (China)
        "oceania": 11,   # AEDT
    }

    contexts = {}
    now = datetime.now(timezone.utc)

    for region, offset in region_offsets.items():
        local_time = now + timedelta(hours=offset)
        hour = local_time.hour

        # Determine what viewers might be doing
        if 5 <= hour < 9:
            activity = "waking up, starting their day, morning coffee"
            energy = "gentle awakening"
        elif 9 <= hour < 12:
            activity = "at work, focused, productive"
            energy = "focused clarity"
        elif 12 <= hour < 14:
            activity = "lunch break, midday pause"
            energy = "relaxed midday"
        elif 14 <= hour < 18:
            activity = "afternoon work, slight fatigue"
            energy = "steady focus"
        elif 18 <= hour < 21:
            activity = "commuting home, dinner, unwinding"
            energy = "transition to relaxation"
        elif 21 <= hour < 24:
            activity = "evening leisure, winding down"
            energy = "calm night"
        else:  # 0-5
            activity = "late night, insomnia, night owls, deep work"
            energy = "nocturnal introspection"

        contexts[region] = {
            "hour": hour,
            "time": local_time.strftime("%I:%M %p"),
            "activity": activity,
            "energy": energy,
        }

    return contexts


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
