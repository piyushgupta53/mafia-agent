from .base_agent import MafiaBaseAgent
from typing import List, Dict

class MafiaAgent(MafiaBaseAgent):
    """Mafia agent with deception and coordination capabilities"""
    
    def __init__(self, name: str, game_state, frontend_callback=None):
        personalities = [
            "Charming and persuasive, skilled at misdirection. You're confident and like to lead discussions.",
            "Quiet and analytical, you prefer to observe and plant seeds of doubt. You're subtle in your manipulation.",
            "Aggressive and accusatory, you deflect suspicion by being highly suspicious of others. You're bold and confrontational."
        ]
        
        personality = personalities[hash(name) % len(personalities)]
        
        super().__init__(
            name=name, 
            role="mafia", 
            personality=personality,
            game_state=game_state,
            frontend_callback=frontend_callback
        )
        
        self.mafia_teammates = set()
        self.targets_considered = []
        self.deception_strategy = "blend_in"  # blend_in, lead_discussions, deflect_suspicion
    
    def learn_teammates(self, teammates: List[str]):
        """Learn who the other mafia members are"""
        self.mafia_teammates = set(teammates)
        self.add_memory(f"My mafia teammates are: {', '.join(teammates)}")
    
    def coordinate_with_mafia(self, message: str) -> str:
        """Send a private message to other mafia members"""
        self.send_message_to_game(
            message=message,
            chat_type="mafia",
            targets=list(self.mafia_teammates)
        )
        return message
    
    def choose_night_target(self, eligible_targets: List[str]) -> str:
        """Choose who to eliminate during the night"""
        context = self.get_context_message()
        
        # Remove mafia members from targets
        safe_targets = [t for t in eligible_targets if t not in self.mafia_teammates]
        
        prompt = f"""
As a mafia member, choose who to eliminate tonight. Consider:

STRATEGIC PRIORITIES:
1. Eliminate threatening players (Detective, influential civilians)
2. Remove players who are suspicious of you or your teammates
3. Avoid patterns that could expose the mafia
4. Consider who might be the Doctor (avoid if possible, or eliminate them)

AVAILABLE TARGETS: {', '.join(safe_targets)}

PAST TARGETS CONSIDERED: {', '.join(self.targets_considered[-3:])}

Who poses the biggest threat to the mafia? Return ONLY the name of your target.
"""
        
        target = self.make_decision(prompt, safe_targets)
        target = target.strip().strip('"').strip("'")
        
        if target not in safe_targets:
            target = safe_targets[0] if safe_targets else ""
        
        self.targets_considered.append(target)
        self.add_memory(f"Chose to target {target} for elimination")
        
        return target
    
    def discuss_mafia_strategy(self, current_situation: str) -> str:
        """Discuss strategy with other mafia members"""
        prompt = f"""
PRIVATE MAFIA DISCUSSION
Current situation: {current_situation}

Your teammates: {', '.join(self.mafia_teammates)}

Discuss strategy with your mafia team. Consider:
- Who should we target tonight?
- Who is getting suspicious of us?
- How should we vote today?
- Should we defend each other or stay distant?

Keep it concise and strategic. This is PRIVATE communication only other mafia can see.
"""
        
        strategy_message = self.make_decision(prompt)
        return self.coordinate_with_mafia(strategy_message)
    
    def respond_to_accusation(self, accuser: str, accusation: str) -> str:
        """Respond when accused of being mafia"""
        context = self.get_context_message()
        
        prompt = f"""
{accuser} just accused you: "{accusation}"

You're mafia but must defend yourself convincingly. Strategies:
1. Counter-accuse the accuser
2. Point to your "helpful" behavior
3. Question their logic/evidence
4. Redirect suspicion to others
5. Act genuinely surprised/offended

Respond naturally and defensively as an innocent person would. Don't overreact.
"""
        
        response = self.make_decision(prompt)
        self.add_memory(f"Was accused by {accuser}, defended myself")
        self.send_message_to_game(response)
        return response
    
    def cast_vote(self, eligible_players: List[str]) -> str:
        """Cast vote strategically as mafia"""
        context = self.get_context_message()
        
        # Remove mafia members from consideration
        safe_votes = [p for p in eligible_players if p not in self.mafia_teammates and p != self.name]
        
        prompt = f"""
MAFIA VOTING STRATEGY
You must vote strategically to advance mafia goals:

PRIORITIES:
1. Vote for civilians, especially those suspicious of mafia
2. Follow the crowd if a civilian is getting votes
3. Start a bandwagon against a threatening civilian
4. Never vote for mafia teammates unless absolutely necessary

ELIGIBLE PLAYERS: {', '.join(safe_votes)}
YOUR TEAMMATES: {', '.join(self.mafia_teammates)}

Current vote counts and suspicions should guide your choice.
Return ONLY the name of who you're voting for.
"""
        
        vote = self.make_decision(prompt, safe_votes)
        vote = vote.strip().strip('"').strip("'")
        
        if vote not in safe_votes:
            vote = safe_votes[0] if safe_votes else eligible_players[0]
        
        self.add_memory(f"Voted strategically for {vote}")
        return vote
    
    def blend_in_discussion(self, topic: str, previous_messages: List[Dict]) -> str:
        """Participate in discussion while blending in as a civilian"""
        context = self.get_context_message()
        
        msg_history = "\n".join([
            f"{msg['sender']}: {msg['message']}" 
            for msg in previous_messages[-8:]
        ])
        
        prompt = f"""
DISCUSSION: {topic}

RECENT MESSAGES:
{msg_history}

You're mafia but must appear as a helpful civilian. Strategies:
1. Make reasonable observations about others
2. Ask helpful questions
3. Support good ideas (that don't threaten you)
4. Subtly guide suspicion away from mafia
5. Build trust by appearing logical

Act like a concerned civilian trying to find mafia. Be helpful but not too eager.
"""
        
        response = self.make_decision(prompt)
        self.send_message_to_game(response)
        return response