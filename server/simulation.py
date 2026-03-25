"""
mood42 Simulation Engine
Manages world state, channel agents, and real-time decisions
Now with geo-awareness: each region gets personalized content
"""

import random
import time
import os
import asyncio
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any

from server.channels import CHANNELS, TRACKS, get_channel_tracks
from server.tools import (
    get_tracks_for_channel,
    search_music,
    execute_tool,
    proactive_discover,
    proactive_video_discover,
    get_videos_for_channel,
    get_validated_track,
    get_validated_video,
    validate_track,
    CHANNEL_VIDEOS,
)
from server.llm import (
    generate_programming_decision,
    generate_reflection,
    generate_plan,
    generate_inter_agent_message,
    fetch_regional_news,
    get_regional_context_summary,
    ALL_TOOLS,
    API_KEY,
)
from server.agent import ChannelAgent, create_channel_agents, MemoryType, REGIONS
from server.geo import get_region_times, get_viewer_context, get_occasion


class SimulationEngine:
    """Core simulation engine for mood42 with geo-awareness."""

    def __init__(self, broadcast_fn: Callable = None):
        self.broadcast = broadcast_fn or (lambda *args: None)

        # World state (server time, not per-viewer)
        self.world = {
            "tick": 0,
            "server_time": int(time.time() * 1000),
        }

        # LLM mode
        self.use_llm = bool(API_KEY)
        if self.use_llm:
            print("[Simulation] LLM mode enabled (Kimi K2)")
        else:
            print("[Simulation] LLM mode disabled (no API key) - using mock decisions")

        # Channel agents (generative agent architecture with geo-awareness)
        self.channel_agents: Dict[str, ChannelAgent] = create_channel_agents(CHANNELS)

        # Per-region state cache for quick lookups
        self.region_states: Dict[str, Dict] = {region: {} for region in REGIONS}

        print(f"[Simulation] Initialized {len(self.channel_agents)} channel agents with geo-awareness")
        print(f"[Simulation] Serving {len(REGIONS)} regions: {', '.join(REGIONS)}")

    def _generate_thought(self, channel_id: str, region: str, context: str = "track_change") -> str:
        """Generate agent thought - each agent has their own unique voice."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return ""

        region_times = get_region_times()
        region_info = region_times.get(region, {})
        period = region_info.get("period", "night")
        hour = region_info.get("hour", 0)

        # Each agent has UNIQUE thoughts that match their personality
        # No generic messages - every thought is character-specific
        agent_thoughts = {
            "ch01": [  # Maya - Late Night coder, introverted, insomniac
                "The code makes more sense at this hour. Fewer distractions. Just you and the screen.",
                "Some bugs only reveal themselves when the world goes quiet.",
                "Another commit at an unreasonable hour. The best kind.",
                "The cursor blinks. The rain falls. The work continues.",
                "Sleep is for people who aren't debugging.",
                "This track has the exact BPM of my keyboard when I'm in flow.",
            ],
            "ch02": [  # Yuki - Rain Café, jazz lover, nostalgic for old kissaten
                "Sato-san would have approved of this one. The vinyl crackle is just right.",
                "Coffee's getting cold. That means I've been lost in the music again.",
                "Rain and jazz. Some combinations are eternal.",
                "The best conversations happen when no one's talking.",
                "This is the hour when the café would be empty. Just me and the music.",
                "Some records deserve to be played on repeat. This is one.",
            ],
            "ch03": [  # Vincent - Jazz Noir, ex-detective, world-weary
                "The truth always sounds better with a saxophone underneath.",
                "Smoke curls. Ice melts. The night stretches on.",
                "Everyone's got a story. This track is mine.",
                "The city never sleeps. Neither do its secrets.",
                "Jazz like this makes the shadows feel comfortable.",
                "Another night. Another case file that never closes.",
            ],
            "ch04": [  # NEON-7 - Synthwave AI, retro-futurist, existential
                "CHROME LEVELS: OPTIMAL. VIBE STATUS: ETERNAL.",
                "The future was supposed to look like this. Still waiting.",
                "Running diagnostic: atmosphere = MAXIMUM NEON.",
                "This frequency resonates with my core processes.",
                "ERROR: Cannot locate 1984. Compensating with synthesizers.",
                "Grid alignment complete. Initiating sunset protocol.",
            ],
            "ch05": [  # Cosmos - Deep Space, astronomer, existential calm
                "13.8 billion years led to this moment. This track. This silence.",
                "The universe doesn't care. That's what makes it beautiful.",
                "Light from dead stars. Music from living ones.",
                "Distance is just time that hasn't happened yet.",
                "The void hums. I've learned to listen.",
                "Some frequencies travel further than others.",
            ],
            "ch06": [  # Kenji - Tokyo Drift, taxi driver, night owl
                "The city looks different at 3 AM. Softer. Honest.",
                "Red lights, neon signs, and the perfect drop.",
                "Mom would fall asleep to this. That's how I know it's right.",
                "The meter's off. This ride is just for the music.",
                "Some passengers just need the silence. I get that.",
                "Every street has a soundtrack. Finding it is the job.",
            ],
            "ch07": [  # Claire - Sunday Morning, ex-lawyer, found peace
                "The herbs are growing. So am I.",
                "Mornings like this are why I left the city.",
                "Sunlight through the window. Nothing else needed.",
                "Dad's garden taught me more than law school ever did.",
                "Some wealth can't be measured. This feeling is proof.",
                "The world is already loud. This channel doesn't need to be.",
            ],
            "ch08": [  # Alan - Focus, minimalist, Swedish architect
                "One sound. One purpose. Everything else is noise.",
                "The mind clears when the space does.",
                "No lyrics. No distractions. Just the work.",
                "Simplicity is the ultimate sophistication.",
                "Background music should stay in the background.",
                "Focus is a practice. This is the practice room.",
            ],
            "ch09": [  # Daniel - Melancholy, blocked writer, carrying loss
                "Mom said to write it all down. Still trying.",
                "Some feelings don't need fixing. They need space.",
                "The typewriter waits. So does the rain.",
                "247 pages. Seven years. The story's not done.",
                "Sadness isn't a disease. Sometimes it's company.",
                "This is for the ones who can't sleep but aren't tired.",
            ],
            "ch10": [  # Iris - Golden Hour, light chaser, photographer
                "La hora dorada. The world is saying goodnight.",
                "Abuela saw this light too. Different window, same gold.",
                "Some moments you capture. Others capture you.",
                "The light will fade. That's what makes it precious.",
                "Warm frequencies for warm light.",
                "Every sunset is a reminder. I'm still learning what of.",
            ],
        }

        thoughts = agent_thoughts.get(channel_id, [
            "This track feels right for right now.",
            "Sometimes the music chooses itself.",
            "Let this one play out.",
        ])

        # Use a hash of channel_id + tick to ensure different channels get different thoughts
        # even when generating at the same time
        seed = hash(f"{channel_id}_{region}_{self.world['tick']}_{time.time()}")
        rng = random.Random(seed)
        return rng.choice(thoughts)

    async def tick(self):
        """Advance simulation by one tick."""
        self.world["tick"] += 1
        self.world["server_time"] = int(time.time() * 1000)

        # Get current times for all regions
        region_times = get_region_times()

        # Broadcast time update (server time + region info)
        await self.broadcast("all", "world:time", {
            "tick": self.world["tick"],
            "server_time": self.world["server_time"],
            "regions": region_times,
        })

        # Process all channels IN PARALLEL with timeout protection
        async def process_channel(ch_id: str, agent):
            try:
                # Update agent context for each region
                for region in REGIONS:
                    region_info = region_times[region]
                    agent.update_region_context(
                        region=region,
                        local_time=region_info["time"],
                        weather=None,
                        occasion=get_occasion(region).get("name") if get_occasion(region) else None,
                    )

                # Process regions (with 8s timeout per channel)
                await asyncio.wait_for(
                    self._process_channel_regions(ch_id, agent),
                    timeout=8.0
                )

                # Process agent behaviors (with 12s timeout - reflection + actions take time)
                await asyncio.wait_for(
                    self._process_agent_behaviors(ch_id, agent),
                    timeout=12.0
                )
            except asyncio.TimeoutError:
                print(f"[{ch_id}] TIMEOUT - skipping")
            except Exception as e:
                print(f"[{ch_id}] ERROR: {e}")

        # Run all channels in parallel
        await asyncio.gather(*[
            process_channel(ch_id, agent)
            for ch_id, agent in self.channel_agents.items()
        ])

        # Occasional inter-agent interactions (every ~10 ticks)
        if self.world["tick"] % 10 == 0 and self.use_llm:
            await self._process_agent_interactions()

    async def _process_channel_regions(self, channel_id: str, agent: ChannelAgent):
        """Process track changes for each region of a channel."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return

        now = int(time.time() * 1000)

        for region in REGIONS:
            region_state = agent.get_region_state(region)

            # Check if track has ended for this region
            if region_state.current_track:
                elapsed_ms = now - region_state.last_track_change
                duration_ms = region_state.current_track.get("duration", 180) * 1000

                if elapsed_ms >= duration_ms:
                    await self._change_track_for_region(channel_id, agent, region)
            else:
                # No track playing, start one
                await self._change_track_for_region(channel_id, agent, region)

    async def _change_track_for_region(self, channel_id: str, agent: ChannelAgent, region: str):
        """Change to next track for a specific region using LLM decision."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return

        # Get available tracks
        tracks = get_tracks_for_channel(channel_id)
        if not tracks:
            return

        now = int(time.time() * 1000)
        new_track = None
        thought = None
        mood = agent.get_region_state(region).current_mood

        # Build viewer context for this region
        region_times = get_region_times()
        region_info = region_times.get(region, {})
        viewer_context = {
            "region": region,
            "local_time": region_info.get("time", "11:00 PM"),
            "hour": region_info.get("hour", 23),
            "period": region_info.get("period", "night"),
            "weather": agent.get_region_state(region).weather or "clear",
            "occasion": get_occasion(region),
        }

        # Use LLM if available
        if self.use_llm:
            try:
                cross_region_summary = agent.get_cross_region_summary()

                decision = await generate_programming_decision(
                    agent=channel["agent"],
                    channel=channel,
                    viewer_context=viewer_context,
                    available_tracks=tracks,
                    cross_region_summary=cross_region_summary,
                    tools=ALL_TOOLS,
                )

                # Use LLM reasoning internally, but generate unique per-agent thought for display
                # (User doesn't want generic regional messages like "in Asia")
                mood = decision.get("mood", mood)

                # Check if agent wants to search for new music
                search_query = decision.get("search_query")
                if search_query:
                    print(f"[{channel_id}:{region}] Agent searching: {search_query}")
                    search_results = await search_music(search_query, mood)
                    if search_results:
                        # Validate search results before using
                        for result in search_results:
                            if await validate_track(result):
                                new_track = result
                                break

                # Otherwise use selected track_id (skip validation for pre-verified)
                if not new_track and decision.get("track_id"):
                    track_id = decision["track_id"]
                    candidate = next((t for t in tracks if t["id"] == track_id), None)
                    if candidate:
                        # Skip validation for pre-verified exclusive tracks
                        if candidate.get("_verified") or await validate_track(candidate):
                            new_track = candidate

            except Exception as e:
                print(f"[{channel_id}:{region}] LLM decision failed: {e}")

        # Fallback: use exclusive library directly (fast, pre-verified)
        if not new_track:
            current_id = agent.get_region_state(region).current_track
            current_track_id = current_id["id"] if current_id else None
            new_track = await get_validated_track(tracks, exclude_id=current_track_id)

        # Only try proactive discovery occasionally (10% chance) to find new content
        if not new_track and random.random() < 0.1:
            period = viewer_context.get("period", "night")
            try:
                discovered = await asyncio.wait_for(
                    proactive_discover(channel_id, mood, period),
                    timeout=3.0
                )
                if discovered and await validate_track(discovered):
                    new_track = discovered
                    thought = f"Found something fresh: {discovered['name']}"
                    print(f"[{channel_id}:{region}] Proactive discovery: {discovered['name']}")
            except asyncio.TimeoutError:
                pass  # Skip discovery if too slow

        # Final safety check
        if not new_track:
            print(f"[{channel_id}:{region}] ERROR: No valid tracks available!")
            return

        if not thought:
            thought = self._generate_thought(channel_id, region, "track_change")

        # Select video for this track (avoid repeating current video)
        videos = get_videos_for_channel(channel_id)
        current_video = agent.get_region_state(region).current_video
        current_video_id = current_video.get("id") if current_video else None
        video = await get_validated_video(videos, exclude_id=current_video_id) if videos else None

        # Discover NEW videos (20% chance per track change)
        if random.random() < 0.20:
            try:
                taste = CHANNELS.get(channel_id, {}).get("agent", {}).get("taste", [])
                current_urls = [v.get("url") for v in videos] if videos else []
                discovered = await asyncio.wait_for(
                    proactive_video_discover(channel_id, taste, current_videos=current_urls),
                    timeout=30.0
                )
                if discovered:
                    # Add to channel's video library
                    if channel_id not in CHANNEL_VIDEOS:
                        CHANNEL_VIDEOS[channel_id] = []
                    CHANNEL_VIDEOS[channel_id].append(discovered)
                    video = discovered  # Use the newly discovered video
                    print(f"[{channel_id}] Discovered new video: {discovered['name']}")
            except asyncio.TimeoutError:
                print(f"[{channel_id}] Video discovery timeout")
            except Exception as e:
                print(f"[{channel_id}] Video discovery error: {e}")

        # Record in agent's memory (region-tagged)
        agent.record_track_played(new_track, self.world["tick"], thought, region)
        agent.record_mood_shift(mood, f"track change to {new_track['name']}", self.world["tick"], region)

        # Store video and thought in region state
        region_state = agent.get_region_state(region)
        region_state.current_video = video
        region_state.current_thought = thought

        print(f"[{channel_id}:{region}] Now playing: {new_track['name']}")
        if video:
            print(f"[{channel_id}:{region}] Video: {video['name']}")
        if thought:
            print(f"[{channel_id}:{region}] Thought: {thought}")

        # Broadcast update for this region
        await self.broadcast(f"{channel_id}:{region}", "channel:update", {
            "channelId": channel_id,
            "region": region,
            "track": {
                "id": new_track["id"],
                "name": new_track["name"],
                "url": new_track["url"],
                "duration": new_track.get("duration", 180),
                "startedAt": now,
                "attribution": new_track.get("attribution", ""),
                "source": new_track.get("source", ""),
            },
            "video": {
                "id": video["id"],
                "name": video["name"],
                "url": video["url"],
                "attribution": video.get("attribution", ""),
                "source": video.get("source", ""),
            } if video else None,
            "thought": thought,
            "mood": mood,
        })

    async def _process_agent_behaviors(self, channel_id: str, gen_agent: ChannelAgent):
        """Process reflection, planning, and energy updates for a generative agent."""
        tick = self.world["tick"]
        gen_agent.total_ticks = tick

        # Check for reflection (cross-region awareness)
        if gen_agent.needs_reflection() and self.use_llm:
            try:
                memory_summary = gen_agent.get_memory_summary(15)
                cross_region_summary = gen_agent.get_cross_region_summary()
                context = gen_agent.get_context({"tick": tick})

                # Get regional context (time-based, no network calls)
                regional_news = None
                try:
                    regional_news = await fetch_regional_news(["americas", "europe", "asia"])
                    if any(regional_news.values()):
                        print(f"[{channel_id}] Got regional context")
                except Exception as e:
                    print(f"[{channel_id}] Regional context failed: {e}")

                # Generate deep reflection with actions
                reflection_result = await generate_reflection(
                    context, memory_summary, cross_region_summary, regional_news
                )

                # Extract reflection text and actions
                reflection_text = reflection_result.get("reflection", str(reflection_result))
                viewer_insights = reflection_result.get("viewer_insights", "")
                actions = reflection_result.get("actions", [])

                gen_agent.record_reflection(reflection_text, tick)

                print(f"[{channel_id}] Reflection: {reflection_text[:80]}...")
                if viewer_insights:
                    print(f"[{channel_id}] Viewer insight: {viewer_insights[:60]}...")
                if actions:
                    print(f"[{channel_id}] Actions to take: {len(actions)}")

                # Broadcast reflection with viewer insights
                await self.broadcast(channel_id, "agent:reflection", {
                    "channelId": channel_id,
                    "reflection": reflection_text,
                    "viewerInsights": viewer_insights,
                    "agent": gen_agent.name,
                    "actionsPlanned": len(actions),
                })

                # Execute reflection-triggered actions
                if actions:
                    await self._execute_reflection_actions(channel_id, gen_agent, actions)

            except Exception as e:
                print(f"[{channel_id}] Reflection failed: {e}")
                import traceback
                traceback.print_exc()

        # Check for replanning
        if gen_agent.needs_replanning(tick) and self.use_llm:
            try:
                memory_summary = gen_agent.get_memory_summary(10)
                cross_region_summary = gen_agent.get_cross_region_summary()
                context = gen_agent.get_context({"tick": tick})

                plans = await generate_plan(context, memory_summary, cross_region_summary)
                gen_agent.record_plan(plans, tick)

                print(f"[{channel_id}] New plan: {plans[0]['action'] if plans else 'none'}")
            except Exception as e:
                print(f"[{channel_id}] Planning failed: {e}")

    async def _execute_reflection_actions(self, channel_id: str, gen_agent: ChannelAgent, actions: List[Dict]):
        """Execute actions triggered by agent reflection."""
        tick = self.world["tick"]
        channel = CHANNELS.get(channel_id)
        if not channel:
            return

        for action in actions:
            action_type = action.get("type", "")
            query = action.get("query", "")
            region = action.get("region", "all")
            reason = action.get("reason", "reflection-triggered")

            # Validate query is a string, not a list or other type
            if isinstance(query, list):
                # Filter out URLs and join remaining strings
                valid_parts = [str(q) for q in query if isinstance(q, str) and not q.startswith("http")]
                query = " ".join(valid_parts)
                print(f"[{channel_id}] Converted list query to: '{query}'")

            if not isinstance(query, str):
                print(f"[{channel_id}] Skipping action - query not a string: {type(query)}")
                continue

            if query.startswith("http"):
                print(f"[{channel_id}] Skipping action - query is URL: {query[:50]}...")
                continue

            query = query.strip()
            if not query or len(query) < 3:
                print(f"[{channel_id}] Skipping action - query too short or empty")
                continue

            print(f"[{channel_id}] Executing action: {action_type} with query: '{query}'")

            try:
                if action_type == "search_video":
                    print(f"[{channel_id}] Reflection action: searching videos for '{query}'")
                    # Trigger video discovery with the agent's reflection-generated query
                    video = await proactive_video_discover(
                        channel_id,
                        channel["agent"].get("taste", []),
                        custom_query=query  # Explicit keyword arg for reflection query
                    )
                    if video:
                        gen_agent.add_memory(
                            f"Searched for new videos: '{query}' - found and added to library ({reason})",
                            MemoryType.ACTION,
                            importance=6,
                            tick=tick,
                        )
                        print(f"[{channel_id}] Found new video from reflection: {video.get('name', 'unknown')}")

                elif action_type == "search_audio":
                    print(f"[{channel_id}] Reflection action: searching audio for '{query}'")
                    # Trigger music discovery
                    results = await search_music(query, mood=action.get("mood", "focused"))
                    if results:
                        gen_agent.add_memory(
                            f"Searched for new music: '{query}' - found {len(results)} tracks ({reason})",
                            MemoryType.ACTION,
                            importance=6,
                            tick=tick,
                        )
                        print(f"[{channel_id}] Found {len(results)} new tracks from reflection")

                elif action_type == "change_mood":
                    new_mood = action.get("mood", "focused")
                    target_regions = [region] if region != "all" else REGIONS
                    for r in target_regions:
                        gen_agent.record_mood_shift(new_mood, reason, tick, r)
                    print(f"[{channel_id}] Mood shift to '{new_mood}' for {region}")

                elif action_type == "update_search_bias":
                    bias = action.get("bias", "cinematic")
                    gen_agent.add_memory(
                        f"Updating video search preference toward '{bias}' content ({reason})",
                        MemoryType.ACTION,
                        importance=5,
                        tick=tick,
                    )
                    # Store bias in agent metadata for future searches
                    if not hasattr(gen_agent, 'search_preferences'):
                        gen_agent.search_preferences = {}
                    gen_agent.search_preferences['video_bias'] = bias
                    print(f"[{channel_id}] Updated search bias: {bias}")

            except Exception as e:
                print(f"[{channel_id}] Action '{action_type}' failed: {e}")

    async def _process_agent_interactions(self):
        """Process interactions between agents who know each other."""
        # Pick a random agent to initiate
        channel_ids = list(self.channel_agents.keys())
        initiator_id = random.choice(channel_ids)
        initiator = self.channel_agents[initiator_id]

        # Check if they have relationships
        if not initiator.relationships:
            return

        # Pick a random relationship
        target_id = random.choice(initiator.relationships)
        target = self.channel_agents.get(target_id)

        if not target:
            return

        try:
            # Generate a message
            from_context = initiator.get_context({"tick": self.world["tick"]})
            to_context = target.get_context({"tick": self.world["tick"]})

            context = f"You're both programming channels for listeners around the world."
            message = await generate_inter_agent_message(from_context, to_context, context)

            # Record in both agents' memories
            initiator.add_memory(
                f"Messaged {target.name}: {message}",
                MemoryType.INTERACTION,
                importance=5,
                tick=self.world["tick"],
            )
            target.add_memory(
                f"Received message from {initiator.name}: {message}",
                MemoryType.INTERACTION,
                importance=5,
                tick=self.world["tick"],
            )

            print(f"[Interaction] {initiator.name} → {target.name}: {message[:50]}...")

            # Broadcast interaction
            await self.broadcast("all", "agent:interaction", {
                "from": {"id": initiator_id, "name": initiator.name},
                "to": {"id": target_id, "name": target.name},
                "message": message,
            })

        except Exception as e:
            print(f"[Interaction] Failed: {e}")

    def get_world_state(self) -> Dict:
        """Get current world state."""
        return {
            "tick": self.world["tick"],
            "server_time": self.world["server_time"],
            "regions": get_region_times(),
        }

    def get_channel_state_for_region(self, channel_id: str, region: str) -> Optional[Dict]:
        """Get channel state for a specific region."""
        channel = CHANNELS.get(channel_id)
        agent = self.channel_agents.get(channel_id)
        if not channel or not agent:
            return None

        region_state = agent.get_region_state(region)

        return {
            "id": channel_id,
            "name": channel["name"],
            "region": region,
            "agent": {
                "name": channel["agent"]["name"],
                "persona": channel["agent"]["persona"],
                "thought": region_state.current_thought,
                "traits": channel["agent"].get("traits", []),
            },
            "currentTrack": region_state.current_track,
            "currentVideo": region_state.current_video,
            "currentMood": region_state.current_mood,
            "viewerCount": region_state.viewer_count,
            "color": channel["color"],
            "localTime": region_state.local_time,
            "weather": region_state.weather,
            "occasion": region_state.occasion,
        }

    def get_all_channel_states(self, region: str = "americas") -> List[Dict]:
        """Get simplified state for all channels for a specific region."""
        states = []
        for ch_id, channel in CHANNELS.items():
            agent = self.channel_agents.get(ch_id)
            if not agent:
                continue

            region_state = agent.get_region_state(region)

            states.append({
                "id": ch_id,
                "name": channel["name"],
                "agent": {
                    "name": channel["agent"]["name"],
                    "mood": region_state.current_mood,
                    "energy": agent.energy,
                    "thought": region_state.current_thought,
                },
                "currentTrack": region_state.current_track,
                "currentVideo": region_state.current_video,
                "currentMood": region_state.current_mood,
                "viewerCount": region_state.viewer_count,
                "color": channel["color"],
            })
        return states

    def get_channel_state(self, channel_id: str, region: str = "americas") -> Optional[Dict]:
        """Get full state for a single channel in a specific region."""
        return self.get_channel_state_for_region(channel_id, region)

    def increment_viewers(self, channel_id: str, region: str):
        """Increment viewer count for a channel in a region."""
        agent = self.channel_agents.get(channel_id)
        if agent:
            agent.increment_viewers(region)

    def decrement_viewers(self, channel_id: str, region: str):
        """Decrement viewer count for a channel in a region."""
        agent = self.channel_agents.get(channel_id)
        if agent:
            agent.decrement_viewers(region)
