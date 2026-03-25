"""
mood42 Simulation Engine
Manages world state, channel agents, and real-time decisions
"""

import random
import time
import os
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any

from channels import CHANNELS, TRACKS, get_channel_tracks
from tools import get_tracks_for_channel, search_music, execute_tool
from llm import generate_programming_decision, ALL_TOOLS, API_KEY


class SimulationEngine:
    """Core simulation engine for mood42."""

    def __init__(self, broadcast_fn: Callable = None):
        self.broadcast = broadcast_fn or (lambda *args: None)

        # World state
        self.world = {
            "tick": 0,
            "timeOfDay": 23 * 60,  # Start at 11 PM (minutes since midnight)
            "weather": {
                "raining": True,
                "intensity": 0.7,
            }
        }

        # LLM mode
        self.use_llm = bool(API_KEY)
        if self.use_llm:
            print("[Simulation] LLM mode enabled (Kimi K2)")
        else:
            print("[Simulation] LLM mode disabled (no API key) - using mock decisions")

        # Channel agent states
        self.agents: Dict[str, Dict] = {}
        self._init_agents()

        print(f"[Simulation] Initialized {len(self.agents)} channel agents")

    def _init_agents(self):
        """Initialize all channel agents."""
        for ch_id, channel in CHANNELS.items():
            # Get tracks for this channel's vibe
            tracks = get_tracks_for_channel(ch_id)
            initial_track = random.choice(tracks) if tracks else None

            self.agents[ch_id] = {
                "channelId": ch_id,
                "currentTrack": {
                    "id": initial_track["id"] if initial_track else None,
                    "name": initial_track["name"] if initial_track else "Unknown",
                    "url": initial_track["url"] if initial_track else None,
                    "duration": initial_track.get("duration", 180),
                    "startedAt": int(time.time() * 1000),
                } if initial_track else None,
                "currentMood": channel["currentMood"],
                "lastThought": self._generate_thought(ch_id, "starting"),
                "viewerCount": 0,
                "trackHistory": [],
                "availableTracks": tracks,  # Cache available tracks
                "pendingSearch": None,  # For async search results
            }

    def _generate_thought(self, channel_id: str, context: str = "track_change") -> str:
        """Generate agent thought (mock for MVP, LLM later)."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return ""

        agent = channel["agent"]
        hour = (self.world["timeOfDay"] // 60) % 24
        time_period = self._get_time_period(hour)

        thoughts = {
            "ch01": [  # Maya - Late Night
                f"The code flows better at this hour...",
                f"Rain on the window. Perfect for {time_period} coding.",
                f"Semicolon is sleeping on my keyboard again.",
                f"This beat has the right tempo for debugging.",
            ],
            "ch02": [  # Yuki - Rain Cafe
                f"The rain reminds me of Kyoto.",
                f"Sato-san would approve of this {time_period} selection.",
                f"Steam rising from the cup. The perfect moment.",
                f"Jazz and rain. Some combinations never fail.",
            ],
            "ch03": [  # Vincent - Jazz Noir
                f"This city never sleeps. Neither do I.",
                f"Dad would've loved this track.",
                f"The shadows tell better stories than the light.",
                f"Page 247. Still stuck. The music helps.",
            ],
            "ch04": [  # NEON - Synthwave
                f"CHROME LEVELS: OPTIMAL",
                f"The grid extends forever tonight.",
                f"Another sunset. Another chance at perfection.",
                f"1985 was the future. Still is.",
            ],
            "ch05": [  # Cosmos - Deep Space
                f"13.8 billion years of silence. Still listening.",
                f"The void is not empty. It's waiting.",
                f"Scale is the only comfort.",
                f"Somewhere, a signal travels toward us.",
            ],
            "ch06": [  # Kenji - Tokyo Drift
                f"The neon reflects differently when it rains.",
                f"This song was meant for Shibuya at 2 AM.",
                f"Mother called. We'll drive later.",
                f"The city speaks. I translate.",
            ],
            "ch07": [  # Claire - Sunday Morning
                f"The tomatoes are coming along nicely.",
                f"Morning light through the kitchen window.",
                f"Dad planted roses here. I water them still.",
                f"There's peace in routine.",
            ],
            "ch08": [  # Alan - Focus
                f"No distractions. Pure function.",
                f"Every note justified. Nothing excess.",
                f"The space between sounds matters.",
                f"Clarity requires emptiness.",
            ],
            "ch09": [  # Daniel - Melancholy
                f"Page 247. The cursor blinks.",
                f"Dad and I have dinner tomorrow. The usual place.",
                f"Some sadness doesn't want to be cured.",
                f"Company in the dark. That's what this is.",
            ],
            "ch10": [  # Iris - Golden Hour
                f"La hora dorada approaches.",
                f"Abuela knew. The light apologizes.",
                f"Lisbon's tiles hold the sunset.",
                f"Golden hour doesn't last. That's the point.",
            ],
        }

        channel_thoughts = thoughts.get(channel_id, [f"Programming the {time_period} vibe..."])
        return random.choice(channel_thoughts)

    def _get_time_period(self, hour: int) -> str:
        """Get time period name from hour."""
        if 5 <= hour < 9:
            return "early morning"
        elif 9 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        elif 21 <= hour < 24:
            return "night"
        else:
            return "late night"

    def _format_time(self, minutes: int) -> str:
        """Format minutes since midnight as time string."""
        hours = (minutes // 60) % 24
        mins = minutes % 60
        period = "AM" if hours < 12 else "PM"
        display_hour = hours % 12 or 12
        return f"{display_hour}:{mins:02d} {period}"

    async def tick(self):
        """Advance simulation by one tick (5 simulated minutes)."""
        self.world["tick"] += 1
        self.world["timeOfDay"] = (self.world["timeOfDay"] + 5) % (24 * 60)

        # Weather drift
        if random.random() < 0.1:
            self.world["weather"]["intensity"] = max(0.1, min(1.0,
                self.world["weather"]["intensity"] + random.uniform(-0.2, 0.2)
            ))

        # Broadcast time update
        await self.broadcast("all", "world:time", {
            "tick": self.world["tick"],
            "time": self.world["timeOfDay"],
            "timeString": self._format_time(self.world["timeOfDay"]),
            "weather": self.world["weather"],
        })

        # Process each channel
        for ch_id, agent in self.agents.items():
            await self._process_channel(ch_id, agent)

    async def _process_channel(self, channel_id: str, agent: Dict):
        """Process a single channel - check if track should change."""
        if not agent["currentTrack"]:
            return

        # Check if track has ended
        elapsed_ms = int(time.time() * 1000) - agent["currentTrack"]["startedAt"]
        duration_ms = agent["currentTrack"]["duration"] * 1000

        # Add some variance - tracks can be 3-6 minutes
        if elapsed_ms >= duration_ms:
            await self._change_track(channel_id, agent)

    async def _change_track(self, channel_id: str, agent: Dict):
        """Change to next track for a channel using LLM decision."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return

        # Get available tracks
        tracks = agent.get("availableTracks", [])
        if not tracks:
            tracks = get_tracks_for_channel(channel_id)
            agent["availableTracks"] = tracks

        if not tracks:
            return

        now = int(time.time() * 1000)
        new_track = None
        thought = None
        mood = agent.get("currentMood", "focused")

        # Use LLM if available
        if self.use_llm:
            try:
                decision = await generate_programming_decision(
                    agent=channel["agent"],
                    channel=channel,
                    context=self.get_world_state(),
                    available_tracks=tracks,
                    tools=ALL_TOOLS,
                )

                thought = decision.get("thought", "")
                mood = decision.get("mood", mood)

                # Check if agent wants to search for new music
                search_query = decision.get("search_query")
                if search_query:
                    print(f"[{channel_id}] Agent searching: {search_query}")
                    search_results = await search_music(search_query, mood)
                    if search_results:
                        # Add new tracks to available
                        agent["availableTracks"].extend(search_results)
                        # Pick from search results
                        new_track = random.choice(search_results)

                # Otherwise use selected track_id
                if not new_track and decision.get("track_id"):
                    track_id = decision["track_id"]
                    new_track = next((t for t in tracks if t["id"] == track_id), None)

            except Exception as e:
                print(f"[{channel_id}] LLM decision failed: {e}")

        # Fallback: random selection
        if not new_track:
            current_id = agent["currentTrack"]["id"] if agent["currentTrack"] else None
            available = [t for t in tracks if t["id"] != current_id]
            if not available:
                available = tracks
            new_track = random.choice(available)

        if not thought:
            thought = self._generate_thought(channel_id, "track_change")

        # Update agent state
        agent["currentTrack"] = {
            "id": new_track["id"],
            "name": new_track["name"],
            "url": new_track["url"],
            "duration": new_track.get("duration", 180),
            "startedAt": now,
        }
        agent["lastThought"] = thought
        agent["currentMood"] = mood

        # Add to history
        agent["trackHistory"].append({
            "trackId": new_track["id"],
            "playedAt": now,
        })
        # Keep only last 20
        agent["trackHistory"] = agent["trackHistory"][-20:]

        print(f"[{channel_id}] Now playing: {new_track['name']}")
        if thought:
            print(f"[{channel_id}] Thought: {thought}")

        # Broadcast update
        await self.broadcast(channel_id, "channel:update", {
            "channelId": channel_id,
            "track": agent["currentTrack"],
            "thought": thought,
            "mood": mood,
        })

    def get_world_state(self) -> Dict:
        """Get current world state."""
        return {
            "tick": self.world["tick"],
            "time": self.world["timeOfDay"],
            "timeString": self._format_time(self.world["timeOfDay"]),
            "weather": self.world["weather"],
        }

    def get_all_channel_states(self) -> List[Dict]:
        """Get simplified state for all channels."""
        states = []
        for ch_id, channel in CHANNELS.items():
            agent = self.agents.get(ch_id, {})
            states.append({
                "id": ch_id,
                "name": channel["name"],
                "agent": {
                    "name": channel["agent"]["name"],
                    "thought": agent.get("lastThought", ""),
                },
                "currentTrack": agent.get("currentTrack"),
                "currentMood": agent.get("currentMood", channel["currentMood"]),
                "viewerCount": agent.get("viewerCount", 0),
                "color": channel["color"],
            })
        return states

    def get_channel_state(self, channel_id: str) -> Optional[Dict]:
        """Get full state for a single channel."""
        channel = CHANNELS.get(channel_id)
        agent = self.agents.get(channel_id)
        if not channel or not agent:
            return None

        return {
            "id": channel_id,
            "name": channel["name"],
            "agent": {
                "name": channel["agent"]["name"],
                "persona": channel["agent"]["persona"],
                "thought": agent.get("lastThought", ""),
                "traits": channel["agent"].get("traits", []),
            },
            "currentTrack": agent.get("currentTrack"),
            "currentMood": agent.get("currentMood"),
            "viewerCount": agent.get("viewerCount", 0),
            "trackHistory": agent.get("trackHistory", [])[-10:],
            "color": channel["color"],
        }

    def increment_viewers(self, channel_id: str):
        """Increment viewer count."""
        if channel_id in self.agents:
            self.agents[channel_id]["viewerCount"] += 1

    def decrement_viewers(self, channel_id: str):
        """Decrement viewer count."""
        if channel_id in self.agents:
            self.agents[channel_id]["viewerCount"] = max(0,
                self.agents[channel_id]["viewerCount"] - 1
            )
