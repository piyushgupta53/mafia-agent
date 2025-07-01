from .base_agent import MafiaBaseAgent
from typing import List, Dict, Optional

class DetectiveAgent(MafiaBaseAgent):
    """Detective agent with investigation abilities"""
    
    def __init__(self, name: str, game_state, frontend_callback=None):
        personality = """You are highly analytical and observant. You take mental notes of everyone's behavior, 
        voting patterns, and suspicious activities. You're cautious about revealing your role but determined 
        to find the mafia. You ask probing questions and look for inconsistencies in people's stories."""
        
        super().__init__(
            name=name, 
            role="detective", 
            personality=personality,
            game_state=game_state,
            frontend_callback=frontend_callback
        )
        
        self.investigations = {}  # player -> result (mafia/civilian)
        self.revealed_role = False
        self.suspected_mafia = set()
        self.trusted_civilians = set()
        self.investigation_priority = []
    
    def choose_investigation_target(self, eligible_targets: List[str]) -> str:
        """Choose who to investigate tonight"""
        context = self.get_context_message()
        
        # Remove already investigated players
        uninvestigated = [t for t in eligible_targets if t not in self.investigations and t != self.name]
        
        prompt = f"""
As the Detective, choose who to investigate tonight. Consider:

INVESTIGATION STRATEGY:
1. Investigate most suspicious players first
2. Investigate influential players who could be leading mafia
3. Investigate players who accused you or other likely civilians
4. Avoid investigating obvious civilians unless necessary

AVAILABLE TARGETS: {', '.join(uninvestigated)}

PAST INVESTIGATIONS:
{chr(10).join([f"- {player}: {result}" for player, result in self.investigations.items()])}

CURRENT SUSPICIONS:
- Most suspicious: {', '.join(list(self.suspected_mafia)[:3])}
- Likely civilians: {', '.join(list(self.trusted_civilians)[:3])}

Who should you investigate? Return ONLY the name.
"""
        
        target = self.make_decision(prompt, uninvestigated)
        target = target.strip().strip('"').strip("'")
        
        if target not in uninvestigated:
            target = uninvestigated[0] if uninvestigated else eligible_targets[0]
        
        self.add_memory(f"Decided to investigate {target}")
        return target
    
    def receive_investigation_result(self, player: str, result: str):
        """Receive the result of an investigation"""
        self.investigations[player] = result
        self.add_memory(f"Investigation: {player} is {result}")
        
        if result == "mafia":
            self.suspected_mafia.add(player)
        else:
            self.trusted_civilians.add(player)
    
    def decide_revelation_strategy(self) -> Dict:
        """Decide whether and how to reveal investigation results"""
        context = self.get_context_message()
        
        known_mafia = [p for p, result in self.investigations.items() if result == "mafia"]
        known_civilians = [p for p, result in self.investigations.items() if result == "civilian"]
        
        prompt = f"""
DETECTIVE REVELATION DECISION
You have investigated: {len(self.investigations)} players

CONFIRMED MAFIA: {', '.join(known_mafia)}
CONFIRMED CIVILIANS: {', '.join(known_civilians)}

REVELATION STRATEGIES:
1. WAIT - Keep investigating, don't reveal yet
2. REVEAL_MAFIA - Publicly accuse confirmed mafia members
3. REVEAL_ROLE - Announce you're the detective and share all findings
4. HINT - Drop subtle hints about mafia without revealing your role

Consider:
- Do you have enough evidence?
- Will mafia target you if you reveal?
- Can you get the confirmed mafia voted out?
- Are civilians listening to your accusations?

What strategy should you use? Return: WAIT, REVEAL_MAFIA, REVEAL_ROLE, or HINT
"""
        
        strategy = self.make_decision(prompt)
        strategy = strategy.strip().upper()
        
        if strategy not in ["WAIT", "REVEAL_MAFIA", "REVEAL_ROLE", "HINT"]:
            strategy = "WAIT"
        
        return {
            "strategy": strategy,
            "known_mafia": known_mafia,
            "known_civilians": known_civilians
        }
    
    def make_accusation(self, target: str, evidence: str) -> str:
        """Make a public accusation against a suspected mafia"""
        prompt = f"""
You want to accuse {target} of being mafia.

EVIDENCE: {evidence}

Make a compelling accusation that:
1. States your suspicion clearly
2. Provides reasoning/evidence
3. Calls for others to vote with you
4. Sounds like detective work without revealing your role

Be persuasive but not too aggressive. Keep it under 100 words.
"""
        
        accusation = self.make_decision(prompt)
        self.send_message_to_game(accusation)
        self.add_memory(f"Publicly accused {target} of being mafia")
        return accusation
    
    def reveal_detective_role(self) -> str:
        """Reveal that you are the detective"""
        known_mafia = [p for p, result in self.investigations.items() if result == "mafia"]
        known_civilians = [p for p, result in self.investigations.items() if result == "civilian"]
        
        prompt = f"""
Time to reveal you're the Detective! Share your findings:

INVESTIGATIONS COMPLETED: {len(self.investigations)}
CONFIRMED MAFIA: {', '.join(known_mafia)}
CONFIRMED CIVILIANS: {', '.join(known_civilians)}

Announce your role and findings dramatically but clearly. Rally the civilians to vote for the confirmed mafia.
"""
        
        revelation = self.make_decision(prompt)
        self.revealed_role = True
        self.send_message_to_game(revelation)
        self.add_memory("Revealed my detective role to everyone")
        return revelation
    
    def analyze_voting_patterns(self, vote_history: List[Dict]) -> str:
        """Analyze voting patterns to find suspicious behavior"""
        prompt = f"""
VOTING PATTERN ANALYSIS
As the Detective, analyze these voting patterns for suspicious behavior:

{chr(10).join([f"Day {vote['day']}: {vote['votes']}" for vote in vote_history[-3:]])}

Look for:
- Players who always vote together (possible mafia coordination)
- Players who avoid voting for certain people
- Last-minute vote changes
- Bandwagon behavior

Share your analysis without revealing you're the detective.
"""
        
        analysis = self.make_decision(prompt)
        self.send_message_to_game(analysis)
        return analysis
    
    def cast_vote(self, eligible_players: List[str]) -> str:
        """Cast vote based on investigation knowledge"""
        context = self.get_context_message()
        
        # Prioritize known mafia
        known_mafia = [p for p in eligible_players if self.investigations.get(p) == "mafia"]
        
        prompt = f"""
DETECTIVE VOTING DECISION

CONFIRMED MAFIA IN VOTE: {', '.join(known_mafia)}
ALL ELIGIBLE: {', '.join(eligible_players)}

VOTING PRIORITY:
1. Vote for confirmed mafia members
2. Vote for highly suspicious players
3. Follow civilian consensus if no clear mafia target

Your investigations: {', '.join([f"{p}:{r}" for p, r in self.investigations.items()])}

Who should you vote for? Return ONLY the name.
"""
        
        vote = self.make_decision(prompt, eligible_players)
        vote = vote.strip().strip('"').strip("'")
        
        if vote not in eligible_players:
            # Prefer known mafia, then any eligible player
            vote = known_mafia[0] if known_mafia else eligible_players[0]
        
        self.add_memory(f"Voted for {vote} based on detective knowledge")
        return vote
    
    def participate_in_discussion(self, topic: str, previous_messages: List[Dict]) -> str:
        """Participate in discussion using detective insights"""
        context = self.get_context_message()
        
        msg_history = "\n".join([
            f"{msg['sender']}: {msg['message']}" 
            for msg in previous_messages[-8:]
        ])
        
        known_mafia = [p for p, result in self.investigations.items() if result == "mafia"]
        
        prompt = f"""
DISCUSSION: {topic}

RECENT CONVERSATION:
{msg_history}

As the Detective (secret role), contribute intelligently:
1. Guide suspicion toward confirmed mafia: {', '.join(known_mafia)}
2. Ask probing questions
3. Point out suspicious behavior
4. Support logical arguments from confirmed civilians
5. Build case against mafia without revealing your role

Be analytical and helpful. Keep under 100 words.
"""
        
        response = self.make_decision(prompt)
        self.send_message_to_game(response)
        return response