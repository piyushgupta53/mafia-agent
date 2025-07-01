from .base_agent import MafiaBaseAgent
from typing import List, Dict


class CivilianAgent(MafiaBaseAgent):
    """Civilian agent with deduction and voting abilities"""

    def __init__(self, name: str, game_state, frontend_callback=None):
        personalities = [
            "You're naturally suspicious and question everything. You like to dig deep into inconsistencies and press people for details.",
            "You're analytical and methodical. You prefer to observe patterns and make logical deductions based on voting behavior and speech patterns.",
            "You're intuitive and go with your gut feelings. You focus on emotional reactions and body language (tone of messages) to detect lies.",
            "You're cooperative and seek consensus. You try to organize group strategy and get everyone working together to find the mafia.",
            "You're bold and confrontational. You're not afraid to make direct accusations and challenge suspicious behavior head-on.",
            "You're cautious and defensive. You're worried about being eliminated and focus on proving your own innocence while finding real threats.",
        ]

        personality = personalities[hash(name) % len(personalities)]

        super().__init__(
            name=name,
            role="civilian",
            personality=personality,
            game_state=game_state,
            frontend_callback=frontend_callback,
        )

        self.suspicion_levels = {}  # player -> suspicion score (1-10)
        self.trust_levels = {}  # player -> trust score (1-10)
        self.voting_patterns = {}  # track how others vote
        self.alliances = set()  # players I'm working with
        self.observations = []  # behavioral observations

    def analyze_behavior(self, player: str, action: str, context: str) -> int:
        """Analyze a player's behavior and return suspicion level (1-10)"""
        prompt = f"""
BEHAVIORAL ANALYSIS: {player}

ACTION: {action}
CONTEXT: {context}

As a civilian trying to find mafia, rate this behavior's suspiciousness (1-10):

SUSPICIOUS INDICATORS (high score):
- Inconsistent statements
- Deflecting questions
- Defending other suspicious players
- Avoiding votes on certain players
- Overly eager to vote for innocent-seeming players
- Changing stories or positions

INNOCENT INDICATORS (low score):
- Logical reasoning
- Consistent behavior
- Helpful questions and observations
- Willingness to admit mistakes
- Cooperative attitude

Rate 1-10 (10 = very suspicious). Return ONLY the number.
"""

        score = self.make_decision(prompt)
        try:
            suspicion_score = int(score.strip())
            suspicion_score = max(1, min(10, suspicion_score))  # Clamp to 1-10
        except:
            suspicion_score = 5  # Default middle score

        self.suspicion_levels[player] = suspicion_score
        self.add_memory(f"{player} behavior suspicion: {suspicion_score}/10 - {action}")
        return suspicion_score

    def track_voting_pattern(self, voter: str, target: str, reasoning: str):
        """Track how someone voted and their reasoning"""
        if voter not in self.voting_patterns:
            self.voting_patterns[voter] = []

        self.voting_patterns[voter].append(
            {"target": target, "reasoning": reasoning, "day": self.game_state.day_count}
        )

        # Analyze the voting pattern
        self.analyze_behavior(voter, f"voted for {target}", reasoning)

    def identify_suspicious_players(self) -> List[str]:
        """Get list of most suspicious players"""
        sorted_suspicions = sorted(
            self.suspicion_levels.items(), key=lambda x: x[1], reverse=True
        )
        return [player for player, score in sorted_suspicions if score >= 6]

    def identify_trusted_players(self) -> List[str]:
        """Get list of most trusted players"""
        sorted_trust = sorted(
            self.trust_levels.items(), key=lambda x: x[1], reverse=True
        )
        return [player for player, score in sorted_trust if score >= 7]

    def form_alliance(self, player: str, reason: str):
        """Form an alliance with another player"""
        self.alliances.add(player)
        self.trust_levels[player] = self.trust_levels.get(player, 5) + 2
        self.add_memory(f"Formed alliance with {player}: {reason}")

    def break_alliance(self, player: str, reason: str):
        """Break an alliance with a player"""
        self.alliances.discard(player)
        self.trust_levels[player] = max(1, self.trust_levels.get(player, 5) - 3)
        self.add_memory(f"Broke alliance with {player}: {reason}")

    def cast_vote(self, eligible_players: List[str]) -> str:
        """Cast vote based on suspicion analysis"""
        context = self.get_context_message()

        # Get most suspicious eligible players
        eligible_suspicions = {
            p: self.suspicion_levels.get(p, 5)
            for p in eligible_players
            if p != self.name
        }

        most_suspicious = max(eligible_suspicions.items(), key=lambda x: x[1])

        prompt = f"""
CIVILIAN VOTING DECISION

ELIGIBLE PLAYERS: {', '.join(eligible_players)}

SUSPICION LEVELS:
{chr(10).join([f"- {p}: {s}/10" for p, s in eligible_suspicions.items()])}

MOST SUSPICIOUS: {most_suspicious[0]} (score: {most_suspicious[1]})

TRUSTED ALLIES: {', '.join(self.alliances)}

Your goal is to eliminate mafia members. Consider:
1. Your suspicion analysis
2. Recent behavior and voting patterns
3. Who your trusted allies suspect
4. Logic and evidence presented

Who should you vote for? Return ONLY the name.
"""

        vote = self.make_decision(prompt, eligible_players)
        vote = vote.strip().strip('"').strip("'")

        if vote not in eligible_players:
            # Default to most suspicious
            vote = most_suspicious[0] if most_suspicious[1] > 5 else eligible_players[0]

        self.add_memory(
            f"Voted for {vote} (suspicion: {eligible_suspicions.get(vote, 'unknown')})"
        )
        return vote

    def participate_in_discussion(
        self, topic: str, previous_messages: List[Dict], discussion_context: str = ""
    ) -> str:
        """Participate in discussion with civilian perspective"""
        context = self.get_context_message()

        msg_history = "\n".join(
            [f"{msg['sender']}: {msg['message']}" for msg in previous_messages[-8:]]
        )

        suspicious_players = self.identify_suspicious_players()
        trusted_players = self.identify_trusted_players()

        prompt = f"""
{discussion_context}

DISCUSSION: {topic}

RECENT CONVERSATION:
{msg_history}

YOUR ANALYSIS:
- Most suspicious: {', '.join(suspicious_players[:3])}
- Most trusted: {', '.join(trusted_players[:3])}
- Current alliances: {', '.join(self.alliances)}

As a civilian, contribute to finding mafia:
1. Share your observations about suspicious behavior
2. Ask probing questions to reveal inconsistencies
3. Challenge weak reasoning or deflection
4. Support logical arguments from trusted players
5. Organize civilian strategy

Be true to your personality. Keep under 100 words.
"""

        response = self.make_decision(prompt)
        self.send_message_to_game(response)
        return response

    def make_accusation(self, target: str) -> str:
        """Make a formal accusation against a suspected mafia"""
        evidence = []
        if target in self.suspicion_levels:
            evidence.append(f"High suspicion level: {self.suspicion_levels[target]}/10")

        if target in self.voting_patterns:
            patterns = self.voting_patterns[target]
            evidence.append(f"Voting patterns: {len(patterns)} votes tracked")

        prompt = f"""
ACCUSATION AGAINST: {target}

EVIDENCE:
{chr(10).join(evidence)}

OBSERVATIONS:
{chr(10).join([obs for obs in self.observations if target in obs][-3:])}

Make a compelling accusation that:
1. States your belief they are mafia
2. Provides specific evidence and reasoning
3. Calls for others to vote with you
4. Addresses potential counter-arguments

Be passionate but logical. Keep under 150 words.
"""

        accusation = self.make_decision(prompt)
        self.send_message_to_game(accusation)
        self.add_memory(f"Formally accused {target} of being mafia")
        return accusation

    def defend_against_accusation(self, accuser: str, accusation: str) -> str:
        """Defend yourself when accused"""
        prompt = f"""
{accuser} accused you: "{accusation}"

Defend yourself as an innocent civilian:
1. Firmly deny being mafia
2. Explain your innocent behavior/reasoning
3. Point out flaws in their logic
4. Redirect suspicion if appropriate
5. Call on allies to support you

Be genuine and defensive as a real innocent person would be.
Keep under 100 words.
"""

        defense = self.make_decision(prompt)
        self.send_message_to_game(defense)
        self.add_memory(f"Defended against accusation from {accuser}")
        return defense

    def organize_civilian_strategy(self, current_situation: str) -> str:
        """Try to organize civilian strategy"""
        trusted = self.identify_trusted_players()
        suspicious = self.identify_suspicious_players()

        prompt = f"""
ORGANIZE CIVILIAN STRATEGY

SITUATION: {current_situation}

TRUSTED PLAYERS: {', '.join(trusted)}
SUSPICIOUS PLAYERS: {', '.join(suspicious)}

Rally the civilians with a strategic plan:
1. Propose voting targets based on evidence
2. Encourage information sharing
3. Suggest coordination among trusted players
4. Address threats to civilian team

Be a natural leader organizing the town. Keep under 120 words.
"""

        strategy = self.make_decision(prompt)
        self.send_message_to_game(strategy)
        self.add_memory("Attempted to organize civilian strategy")
        return strategy
