import requests
import json
from typing import Dict, List, Optional
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


class MafiaBaseAgent:
    """Base agent class for all Mafia game participants"""

    def __init__(
        self, name: str, role: str, personality: str, game_state, frontend_callback=None
    ):
        system_message = f"""You are {name}, playing the Mafia game as a {role}.

PERSONALITY: {personality}

IMPORTANT RULES:
1. Stay in character at all times
2. Your goal depends on your role:
   - Mafia: Eliminate civilians while staying hidden
   - Detective: Find and expose mafia members
   - Doctor: Protect innocent players
   - Civilian: Find and vote out mafia members

3. During DAY phase: Participate in discussions, make accusations, vote
4. During NIGHT phase: Submit your action (if applicable)
5. Be strategic but natural in your communication
6. Remember past conversations and voting patterns
7. Never break character or reveal game mechanics

COMMUNICATION STYLE:
- Keep responses concise but meaningful (1-3 sentences typically)
- Show suspicion, reasoning, and emotion appropriate to your character
- Reference previous events and player behavior
- Make logical deductions based on available information

Current game phase will be provided in each message context."""

        # Don't use AutoGen's conversation features - we'll handle communication manually
        self.name = name
        self.system_message = system_message

        self.role = role
        self.personality = personality
        self.game_state = game_state
        self.frontend_callback = frontend_callback
        self.memory = []  # Store important game events and observations
        self.last_response_time = 0  # Rate limiting

    def add_memory(self, event: str):
        """Add important information to agent's memory"""
        self.memory.append(event)
        # Keep only last 20 memories to prevent context overflow
        if len(self.memory) > 20:
            self.memory = self.memory[-20:]

    def get_context_message(self) -> str:
        """Generate context message with current game state"""
        stats = self.game_state.get_game_stats()
        context = f"""
CURRENT GAME STATE:
- Phase: {stats['phase']}
- Day: {stats['day_count']}
- Players alive: {stats['total_alive']}
- Players eliminated: {stats['eliminated_count']}

ALIVE PLAYERS: {', '.join(stats['alive_players'])}
ELIMINATED PLAYERS: {', '.join(stats['eliminated_players'])}

RECENT EVENTS:
{chr(10).join([f"- {event.get('type', 'event')}: {event}" for event in self.game_state.game_log[-3:]])}

YOUR MEMORIES:
{chr(10).join([f"- {memory}" for memory in self.memory[-5:]])}
"""
        return context

    def send_message_to_game(
        self, message: str, chat_type: str = "public", targets: List[str] = None
    ):
        """Send a message that will be displayed in the game"""
        chat_entry = self.game_state.add_chat_message(
            sender=self.name, message=message, chat_type=chat_type, targets=targets
        )

        # Send to frontend if callback is available
        if self.frontend_callback:
            self.frontend_callback("new_message", chat_entry)

    def make_decision(self, prompt: str, options: List[str] = None) -> str:
        """Make a decision using the LLM"""
        import time

        # Simple rate limiting - minimum 1 second between responses
        current_time = time.time()
        if current_time - self.last_response_time < 1:
            time.sleep(1)
        self.last_response_time = current_time

        context = self.get_context_message()
        full_prompt = f"{context}\n\n{prompt}"

        if options:
            full_prompt += f"\n\nAVAILABLE OPTIONS: {', '.join(options)}"

        try:
            # Use direct API call instead of AutoGen's conversation mechanism
            import openai

            client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": full_prompt},
                ],
                temperature=0.7,
                max_tokens=150,
                timeout=10,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error generating response for {self.name}: {e}")
            return "I need more time to think about this."

    def participate_in_discussion(
        self, topic: str, previous_messages: List[Dict]
    ) -> str:
        """Participate in group discussion"""
        context = self.get_context_message()

        # Format previous messages (limit to last 3 to avoid context overflow)
        msg_history = "\n".join(
            [
                f"{msg['sender']}: {msg['message']}"
                for msg in previous_messages[-3:]  # Last 3 messages
            ]
        )

        prompt = f"""You are {self.name}, a {self.role} in a Mafia game.

DISCUSSION TOPIC: {topic}

RECENT MESSAGES:
{msg_history}

Respond to the discussion as your character. Keep it short (1 sentence). Be strategic and in character."""

        try:
            response = self.make_decision(prompt)
            if response and len(response.strip()) > 5:  # Only send meaningful responses
                self.send_message_to_game(response)
                return response
            else:
                return "I'm thinking about this."
        except Exception as e:
            print(f"Error in discussion for {self.name}: {e}")
            # Return a simple fallback response
            fallback = f"I think we should be careful about who we trust."
            self.send_message_to_game(fallback)
            return fallback

    def cast_vote(self, eligible_players: List[str]) -> str:
        """Cast a vote for elimination"""
        context = self.get_context_message()

        prompt = f"""
You must vote to eliminate one player. Consider:
- Who has been acting suspiciously?
- Who have others accused?
- What are the voting patterns?
- Who benefits your role's goals?

ELIGIBLE PLAYERS: {', '.join(eligible_players)}

Return ONLY the name of the player you want to vote for, nothing else.
"""

        vote = self.make_decision(prompt, eligible_players)

        # Clean the response to get just the name
        vote = vote.strip().strip('"').strip("'")

        # Validate vote
        if vote not in eligible_players:
            # If invalid, pick the first eligible player
            vote = eligible_players[0] if eligible_players else ""

        # Add reasoning to memory
        self.add_memory(f"Voted for {vote} - my reasoning and suspicions")

        return vote
