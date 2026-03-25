"""
mood42 Simulation Engine
Manages world state, channel agents, and real-time decisions
Now with geo-awareness: each region gets personalized content
"""

import random
import time
import os
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any

from server.channels import CHANNELS, TRACKS, get_channel_tracks
from server.tools import (
    get_tracks_for_channel,
    search_music,
    execute_tool,
    proactive_discover,
    get_videos_for_channel,
    get_validated_track,
    get_validated_video,
    validate_track,
)
from server.llm import (
    generate_programming_decision,
    generate_reflection,
    generate_plan,
    generate_inter_agent_message,
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
        """Generate agent thought (mock for MVP, LLM later)."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return ""

        agent = channel["agent"]
        region_times = get_region_times()
        region_info = region_times.get(region, {})
        period = region_info.get("period", "night")

        # Region-aware thoughts
        thoughts = {
            "ch01": {  # Maya - Late Night
                "americas": [
                    f"The night owls on the east coast are still up...",
                    f"LA's just getting into the {period} groove.",
                    f"Perfect coding hour for the Americas.",
                ],
                "europe": [
                    f"London {period}. Grey skies, warm beats.",
                    f"Berlin's winding down... or just starting.",
                    f"Paris cafes would love this right now.",
                ],
                "asia": [
                    f"Tokyo salarymen need this focus energy.",
                    f"Seoul's neon is hitting different tonight.",
                    f"Singapore humidity calls for chill vibes.",
                ],
                "oceania": [
                    f"Sydney's {period} feels right for this.",
                    f"Melbourne coffee culture, meet lo-fi.",
                    f"Auckland vibes incoming.",
                ],
            },
            "default": {
                "americas": [f"Programming the {period} vibe for the Americas..."],
                "europe": [f"Curating for Europe's {period}..."],
                "asia": [f"Setting the mood for Asia's {period}..."],
                "oceania": [f"Oceania's {period} needs this..."],
            }
        }

        channel_thoughts = thoughts.get(channel_id, thoughts["default"])
        region_thoughts = channel_thoughts.get(region, [f"Programming the {period} vibe..."])
        return random.choice(region_thoughts)

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

        # Process each channel
        for ch_id, agent in self.channel_agents.items():
            # Update agent context for each region
            for region in REGIONS:
                region_info = region_times[region]
                agent.update_region_context(
                    region=region,
                    local_time=region_info["time"],
                    weather=None,  # Could fetch real weather
                    occasion=get_occasion(region).get("name") if get_occasion(region) else None,
                )

            # Check if any region needs a track change
            await self._process_channel_regions(ch_id, agent)

            # Process generative agent behaviors (reflection, planning)
            await self._process_agent_behaviors(ch_id, agent)

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

                thought = decision.get("thought", "")
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

                # Otherwise use selected track_id (validate it first)
                if not new_track and decision.get("track_id"):
                    track_id = decision["track_id"]
                    candidate = next((t for t in tracks if t["id"] == track_id), None)
                    if candidate and await validate_track(candidate):
                        new_track = candidate

            except Exception as e:
                print(f"[{channel_id}:{region}] LLM decision failed: {e}")

        # Try proactive discovery if no track selected yet
        if not new_track:
            period = viewer_context.get("period", "night")
            discovered = await proactive_discover(channel_id, mood, period)
            if discovered and await validate_track(discovered):
                new_track = discovered
                thought = f"Found something fresh: {discovered['name']}"
                print(f"[{channel_id}:{region}] Proactive discovery: {discovered['name']}")

        # Fallback: get a VALIDATED track from the library
        if not new_track:
            current_id = agent.get_region_state(region).current_track
            current_track_id = current_id["id"] if current_id else None
            new_track = await get_validated_track(tracks, exclude_id=current_track_id)

        # Final safety check
        if not new_track:
            print(f"[{channel_id}:{region}] ERROR: No valid tracks available!")
            return

        if not thought:
            thought = self._generate_thought(channel_id, region, "track_change")

        # Select VALIDATED video for this track
        videos = get_videos_for_channel(channel_id)
        video = await get_validated_video(videos) if videos else None

        # Record in agent's memory (region-tagged)
        agent.record_track_played(new_track, self.world["tick"], thought, region)
        agent.record_mood_shift(mood, f"track change to {new_track['name']}", self.world["tick"], region)

        # Store video in region state
        region_state = agent.get_region_state(region)
        region_state.current_video = video

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
            },
            "video": {
                "id": video["id"],
                "name": video["name"],
                "url": video["url"],
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

                reflection = await generate_reflection(context, memory_summary, cross_region_summary)
                gen_agent.record_reflection(reflection, tick)

                print(f"[{channel_id}] Reflection: {reflection[:80]}...")

                # Broadcast reflection
                await self.broadcast(channel_id, "agent:reflection", {
                    "channelId": channel_id,
                    "reflection": reflection,
                    "agent": gen_agent.name,
                })
            except Exception as e:
                print(f"[{channel_id}] Reflection failed: {e}")

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
                "thought": None,  # Get from recent memories
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
                },
                "currentTrack": region_state.current_track,
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
