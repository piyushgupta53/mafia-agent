import asyncio
import random
import time
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import threading

from .game_state import GameState, GamePhase
from .agents.narrator_agent import NarratorAgent
from .agents.mafia_agent import MafiaAgent
from .agents.detective_agent import DetectiveAgent
from .agents.doctor_agent import DoctorAgent
from .agents.civilian_agent import CivilianAgent
from config import GAME_CONFIG


class MafiaGameController:
    """Main controller for the Mafia game"""

    def __init__(self, frontend_callback: Optional[Callable] = None):
        self.game_state = GameState()
        self.frontend_callback = frontend_callback
        self.agents: Dict[str, any] = {}
        self.agent_threads: Dict[str, threading.Thread] = {}
        self.game_running = False
        self.executor = ThreadPoolExecutor(max_workers=15)

        # Game timing
        self.discussion_time = GAME_CONFIG["discussion_time"]
        self.voting_time = GAME_CONFIG["voting_time"]
        self.max_discussion_rounds = GAME_CONFIG["max_discussion_rounds"]
        self.response_timeout = GAME_CONFIG["response_timeout"]

        # Phase management
        self.phase_lock = threading.Lock()
        self.votes_submitted = {}
        self.night_actions_submitted = {}

    def create_agents(self):
        """Create all agents for the game"""
        # Create narrator
        self.agents["Narrator"] = NarratorAgent(
            "Narrator", self.game_state, self.frontend_callback
        )

        # Create player names
        player_names = [
            "Alice",
            "Bob",
            "Charlie",
            "Diana",
            "Eve",
            "Frank",
            "Grace",
            "Henry",
            "Iris",
            "Jack",
            "Kate",
            "Liam",
            "Maya",
        ]

        random.shuffle(player_names)

        # Assign roles
        roles = (
            ["mafia"] * GAME_CONFIG["mafia_count"]
            + ["detective"] * GAME_CONFIG["detective_count"]
            + ["doctor"] * GAME_CONFIG["doctor_count"]
            + ["civilian"] * GAME_CONFIG["civilian_count"]
        )

        random.shuffle(roles)

        # Create agents
        for i, name in enumerate(
            player_names[: GAME_CONFIG["total_players"] - 1]
        ):  # -1 for narrator
            role = roles[i]

            if role == "mafia":
                agent = MafiaAgent(name, self.game_state, self.frontend_callback)
            elif role == "detective":
                agent = DetectiveAgent(name, self.game_state, self.frontend_callback)
            elif role == "doctor":
                agent = DoctorAgent(name, self.game_state, self.frontend_callback)
            else:  # civilian
                agent = CivilianAgent(name, self.game_state, self.frontend_callback)

            self.agents[name] = agent
            self.game_state.add_player(name, role, agent)

        # Inform mafia members about each other
        mafia_members = [
            name
            for name, agent in self.agents.items()
            if hasattr(agent, "role") and agent.role == "mafia"
        ]

        for name in mafia_members:
            teammates = [m for m in mafia_members if m != name]
            self.agents[name].learn_teammates(teammates)

    def send_update_to_frontend(self, event_type: str, data: any):
        """Send updates to the frontend"""
        if self.frontend_callback:
            self.frontend_callback(event_type, data)

    async def start_game(self):
        """Start the game"""
        print("🎮 Starting Mafia Game...")

        self.create_agents()
        self.game_running = True

        # Announce game start
        player_names = [name for name in self.agents.keys() if name != "Narrator"]
        self.agents["Narrator"].announce_game_start(player_names)

        # Send initial game state
        self.send_update_to_frontend("game_state", self.game_state.to_dict())

        # Start with first night
        await self.run_first_night()

        # Main game loop
        while self.game_running:
            winner = self.game_state.check_win_condition()
            if winner:
                await self.end_game(winner)
                break

            await self.run_day_phase()

            winner = self.game_state.check_win_condition()
            if winner:
                await self.end_game(winner)
                break

            await self.run_night_phase()

    async def run_first_night(self):
        """Run the special first night phase"""
        print("🌙 First Night Phase")
        self.game_state.phase = GamePhase.FIRST_NIGHT

        # Mafia learn each other
        mafia_members = list(self.game_state.mafia_members)
        if len(mafia_members) > 1:
            # Let mafia introduce themselves
            await self.facilitate_mafia_meeting(
                "Learn your teammates and discuss initial strategy"
            )

        await asyncio.sleep(2)  # Brief pause

        # Transition to first day
        self.game_state.day_count = 1
        self.game_state.phase = GamePhase.DAY
        self.agents["Narrator"].announce_phase_transition(
            "day", self.game_state.day_count
        )

        self.send_update_to_frontend("game_state", self.game_state.to_dict())

    async def run_day_phase(self):
        """Run a day phase with discussion and voting"""
        print(f"☀️ Day {self.game_state.day_count} Phase")

        # Discussion period
        await self.run_discussion("Who do you suspect and why?", self.discussion_time)

        # Voting phase
        await self.run_voting()

        # Check for elimination
        eliminated = self.game_state.get_majority_vote_target()
        if eliminated:
            vote_counts = self.game_state.get_vote_counts()
            self.agents["Narrator"].announce_elimination(eliminated, vote_counts)
            self.game_state.eliminate_player(eliminated)

        self.game_state.clear_votes()
        self.send_update_to_frontend("game_state", self.game_state.to_dict())

    async def run_night_phase(self):
        """Run a night phase with actions"""
        print(f"🌙 Night {self.game_state.day_count} Phase")
        self.game_state.phase = GamePhase.NIGHT
        self.agents["Narrator"].announce_phase_transition(
            "night", self.game_state.day_count
        )

        # Collect night actions
        await self.collect_night_actions()

        # Resolve night actions
        results = self.resolve_night_actions()

        # Announce results
        self.agents["Narrator"].announce_night_results(
            results.get("eliminated"),
            results.get("protected"),
            results.get("investigation"),
        )

        # Apply eliminations
        if results.get("eliminated") and results.get("eliminated") != results.get(
            "protected"
        ):
            self.game_state.eliminate_player(results["eliminated"])

        # Send investigation result to detective
        if results.get("investigation"):
            detective_name = results["investigation"]["detective"]
            target = results["investigation"]["target"]
            result = results["investigation"]["result"]
            self.agents[detective_name].receive_investigation_result(target, result)

        self.game_state.clear_night_actions()
        self.game_state.day_count += 1
        self.game_state.phase = GamePhase.DAY

        self.send_update_to_frontend("game_state", self.game_state.to_dict())

    async def run_discussion(self, topic: str, duration: int):
        """Run a discussion period"""
        print(f"💬 Discussion: {topic}")
        self.agents["Narrator"].facilitate_discussion(topic, duration)

        # Get alive players
        alive_players = [
            name for name in self.game_state.alive_players if name != "Narrator"
        ]

        # Track who has spoken to ensure fairness
        players_spoken = set()

        # Run discussion for specified duration
        start_time = time.time()
        discussion_rounds = 0

        # Phase 1: Ensure every player gets to speak at least once
        print("🔄 Phase 1: Initial statements from all players")
        for speaker in alive_players:
            if speaker in self.agents:
                try:
                    # Add timeout to prevent hanging
                    await asyncio.wait_for(
                        self.run_agent_discussion(speaker, topic),
                        timeout=self.response_timeout,
                    )
                    players_spoken.add(speaker)
                    await asyncio.sleep(1)  # Brief pause between speakers
                except asyncio.TimeoutError:
                    print(f"Timeout in discussion for {speaker}")
                except Exception as e:
                    print(f"Error in discussion for {speaker}: {e}")

        # Phase 2: Follow-up discussions and responses
        print("🔄 Phase 2: Follow-up discussions and responses")
        remaining_time = duration - (time.time() - start_time)

        while remaining_time > 0 and discussion_rounds < self.max_discussion_rounds:
            # Check for agents who should respond to accusations
            recent_messages = self.game_state.chat_history[-10:]
            priority_speakers = []

            for player in alive_players:
                if self.should_agent_respond(player, recent_messages):
                    priority_speakers.append(player)

            # Select players who haven't spoken recently for follow-up
            available_speakers = [p for p in alive_players if p not in players_spoken]

            if not available_speakers:
                # If everyone has spoken, reset and allow everyone to speak again
                players_spoken.clear()
                available_speakers = alive_players

            # Prioritize agents who need to respond to accusations
            if priority_speakers:
                speakers = priority_speakers[:2]  # Allow up to 2 priority responses
            else:
                # Select 2-3 players for this round
                num_speakers = min(3, len(available_speakers))
                speakers = random.sample(available_speakers, num_speakers)

            # Run discussions sequentially to avoid conflicts
            for speaker in speakers:
                if speaker in self.agents:
                    try:
                        # Add timeout to prevent hanging
                        await asyncio.wait_for(
                            self.run_agent_discussion(speaker, topic),
                            timeout=self.response_timeout,
                        )
                        players_spoken.add(speaker)
                        await asyncio.sleep(1)  # Brief pause between speakers
                    except asyncio.TimeoutError:
                        print(f"Timeout in discussion for {speaker}")
                    except Exception as e:
                        print(f"Error in discussion for {speaker}: {e}")

            discussion_rounds += 1
            await asyncio.sleep(3)  # Longer pause between rounds
            remaining_time = duration - (time.time() - start_time)

    async def run_agent_discussion(self, agent_name: str, topic: str):
        """Run discussion for a single agent"""
        try:
            agent = self.agents[agent_name]
            recent_messages = self.game_state.chat_history[-10:]

            # Get discussion stats to provide context
            discussion_stats = self.get_discussion_stats()

            # Add discussion context to help agents understand participation
            discussion_context = f"""
DISCUSSION CONTEXT:
- Topic: {topic}
- Total players: {discussion_stats['total_players']}
- Most active speaker: {discussion_stats['most_active']}
- Recent messages: {len(recent_messages)}
"""

            # Run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                agent.participate_in_discussion,
                topic,
                recent_messages,
                discussion_context,
            )

            self.send_update_to_frontend("game_state", self.game_state.to_dict())

        except Exception as e:
            print(f"Error in discussion for {agent_name}: {e}")

    async def run_voting(self):
        """Run the voting phase"""
        print("🗳️ Voting Phase")
        eligible_players = [p for p in self.game_state.alive_players if p != "Narrator"]
        self.agents["Narrator"].announce_voting_phase(eligible_players)

        # Collect votes from all alive players
        self.votes_submitted.clear()

        # Collect votes sequentially with small delays to make them visible
        for voter in eligible_players:
            if voter in self.agents:
                await self.collect_vote(voter, eligible_players)
                # Send update after each vote to show individual votes
                self.send_update_to_frontend("game_state", self.game_state.to_dict())
                # Small delay to make votes visible
                await asyncio.sleep(1.5)

        self.send_update_to_frontend("game_state", self.game_state.to_dict())

    async def collect_vote(self, voter: str, eligible_players: List[str]):
        """Collect vote from a single player"""
        try:
            agent = self.agents[voter]

            # Run in thread
            loop = asyncio.get_event_loop()
            vote = await loop.run_in_executor(
                self.executor,
                agent.cast_vote,
                [p for p in eligible_players if p != voter],
            )

            self.game_state.add_vote(voter, vote)
            self.votes_submitted[voter] = vote

            # Announce vote
            vote_msg = f"{voter} votes for {vote}"
            self.game_state.add_chat_message("Narrator", vote_msg, "public")

        except Exception as e:
            print(f"Error collecting vote from {voter}: {e}")
            # Default vote
            if eligible_players:
                default_vote = (
                    eligible_players[0]
                    if eligible_players[0] != voter
                    else (
                        eligible_players[1]
                        if len(eligible_players) > 1
                        else eligible_players[0]
                    )
                )
                self.game_state.add_vote(voter, default_vote)

    async def collect_night_actions(self):
        """Collect night actions from all players"""
        self.night_actions_submitted.clear()

        alive_players = [p for p in self.game_state.alive_players if p != "Narrator"]
        tasks = []

        for player in alive_players:
            agent = self.agents[player]

            if agent.role == "mafia":
                task = self.collect_mafia_action(player, alive_players)
                tasks.append(task)
            elif agent.role == "detective":
                task = self.collect_detective_action(player, alive_players)
                tasks.append(task)
            elif agent.role == "doctor":
                task = self.collect_doctor_action(player, alive_players)
                tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def collect_mafia_action(self, mafia_name: str, alive_players: List[str]):
        """Collect action from mafia member"""
        try:
            agent = self.agents[mafia_name]
            targets = [
                p for p in alive_players if p not in self.game_state.mafia_members
            ]

            loop = asyncio.get_event_loop()
            target = await loop.run_in_executor(
                self.executor, agent.choose_night_target, targets
            )

            self.game_state.add_night_action(mafia_name, "eliminate", target)

        except Exception as e:
            print(f"Error collecting mafia action from {mafia_name}: {e}")

    async def collect_detective_action(
        self, detective_name: str, alive_players: List[str]
    ):
        """Collect action from detective"""
        try:
            agent = self.agents[detective_name]
            targets = [p for p in alive_players if p != detective_name]

            loop = asyncio.get_event_loop()
            target = await loop.run_in_executor(
                self.executor, agent.choose_investigation_target, targets
            )

            self.game_state.add_night_action(detective_name, "investigate", target)

        except Exception as e:
            print(f"Error collecting detective action from {detective_name}: {e}")

    async def collect_doctor_action(self, doctor_name: str, alive_players: List[str]):
        """Collect action from doctor"""
        try:
            agent = self.agents[doctor_name]

            loop = asyncio.get_event_loop()
            target = await loop.run_in_executor(
                self.executor, agent.choose_protection_target, alive_players
            )

            self.game_state.add_night_action(doctor_name, "protect", target)

        except Exception as e:
            print(f"Error collecting doctor action from {doctor_name}: {e}")

    def resolve_night_actions(self) -> Dict:
        """Resolve all night actions and return results"""
        results = {}

        # Get mafia target (majority vote among mafia)
        mafia_targets = {}
        for player, action in self.game_state.night_actions.items():
            if action["action"] == "eliminate" and action["target"]:
                target = action["target"]
                mafia_targets[target] = mafia_targets.get(target, 0) + 1

        if mafia_targets:
            eliminated = max(mafia_targets.items(), key=lambda x: x[1])[0]
            results["eliminated"] = eliminated

        # Get doctor protection
        for player, action in self.game_state.night_actions.items():
            if action["action"] == "protect" and action["target"]:
                results["protected"] = action["target"]
                self.game_state.protected_player = action["target"]
                break

        # Get detective investigation
        for player, action in self.game_state.night_actions.items():
            if action["action"] == "investigate" and action["target"]:
                target = action["target"]
                is_mafia = target in self.game_state.mafia_members
                results["investigation"] = {
                    "detective": player,
                    "target": target,
                    "result": "mafia" if is_mafia else "civilian",
                }
                break

        return results

    async def facilitate_mafia_meeting(self, topic: str):
        """Facilitate a private mafia meeting"""
        mafia_members = list(self.game_state.mafia_members)

        if len(mafia_members) > 1:
            # Random mafia member starts discussion
            speaker = random.choice(mafia_members)
            agent = self.agents[speaker]

            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self.executor, agent.discuss_mafia_strategy, topic
                )
            except Exception as e:
                print(f"Error in mafia meeting: {e}")

    async def end_game(self, winner: str):
        """End the game and announce winner"""
        print(f"🏁 Game Over - {winner} wins!")

        self.game_state.phase = GamePhase.GAME_OVER
        self.game_running = False

        final_stats = self.game_state.get_game_stats()
        self.agents["Narrator"].announce_game_end(winner, final_stats)

        self.send_update_to_frontend(
            "game_over", {"winner": winner, "stats": final_stats}
        )

        # Cleanup
        self.executor.shutdown(wait=False)

    def should_agent_respond(
        self, agent_name: str, recent_messages: List[Dict]
    ) -> bool:
        """Check if an agent should respond based on recent messages"""
        if not recent_messages:
            return False

        # Check if agent was mentioned or accused in recent messages
        for msg in recent_messages[-3:]:  # Check last 3 messages
            message_text = msg["message"].lower()
            if agent_name.lower() in message_text:
                # Check for accusation patterns
                accusation_words = [
                    "accuse",
                    "suspicious",
                    "mafia",
                    "lying",
                    "defend",
                    "explain",
                ]
                if any(word in message_text for word in accusation_words):
                    return True

        return False

    def get_discussion_stats(self) -> Dict:
        """Get statistics about discussion participation"""
        alive_players = [
            name for name in self.game_state.alive_players if name != "Narrator"
        ]

        # Count messages per player in recent chat history
        player_message_counts = {}
        for player in alive_players:
            player_message_counts[player] = 0

        # Count recent messages (last 20 messages)
        recent_messages = self.game_state.chat_history[-20:]
        for msg in recent_messages:
            if msg["sender"] in player_message_counts:
                player_message_counts[msg["sender"]] += 1

        return {
            "total_players": len(alive_players),
            "player_message_counts": player_message_counts,
            "most_active": (
                max(player_message_counts.items(), key=lambda x: x[1])[0]
                if player_message_counts
                else None
            ),
            "least_active": (
                min(player_message_counts.items(), key=lambda x: x[1])[0]
                if player_message_counts
                else None
            ),
        }
