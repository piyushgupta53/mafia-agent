from .base_agent import MafiaBaseAgent
from typing import List, Dict


class DoctorAgent(MafiaBaseAgent):
    """Doctor agent with healing/protection abilities"""

    def __init__(self, name: str, game_state, frontend_callback=None):
        personality = """You are protective and strategic, focused on saving innocent lives. 
        You're naturally helpful and caring, often showing concern for other players' safety. 
        You think carefully about who might be targeted by the mafia and try to stay hidden 
        while maximizing your protective impact. You're observant of who seems most valuable 
        to the civilian team."""

        super().__init__(
            name=name,
            role="doctor",
            personality=personality,
            game_state=game_state,
            frontend_callback=frontend_callback,
        )

        self.protection_history = []
        self.suspected_roles = {}  # player -> suspected role
        self.valuable_civilians = set()
        self.revealed_role = False

    def choose_protection_target(self, eligible_targets: List[str]) -> str:
        """Choose who to protect tonight"""
        context = self.get_context_message()

        # Remove self from targets (can't protect yourself in most variants)
        targets = [t for t in eligible_targets if t != self.name]

        prompt = f"""
As the Doctor, choose who to protect tonight. Consider:

PROTECTION PRIORITIES:
1. Likely Detective (if you can identify them)
2. Strong civilian leaders who are finding mafia
3. Players being heavily suspected but seem innocent
4. Yourself only if absolutely necessary

AVAILABLE TARGETS: {', '.join(targets)}

PREVIOUS PROTECTIONS: {', '.join(self.protection_history[-3:])}

SUSPECTED ROLES:
{chr(10).join([f"- {player}: {role}" for player, role in self.suspected_roles.items()])}

VALUABLE CIVILIANS: {', '.join(self.valuable_civilians)}

Who needs protection most? Consider who mafia might target.
Return ONLY the name.
"""

        target = self.make_decision(prompt, targets)
        target = target.strip().strip('"').strip("'")

        if target not in targets:
            target = targets[0] if targets else self.name

        self.protection_history.append(target)
        self.add_memory(f"Protected {target} from mafia attack")
        return target

    def analyze_who_needs_protection(self, recent_events: List[Dict]) -> str:
        """Analyze who might be targeted by mafia"""
        prompt = f"""
THREAT ASSESSMENT
Recent game events: {recent_events}

As the Doctor, analyze who mafia might target tonight:

LIKELY TARGETS:
1. Players who made strong accusations against suspected mafia
2. Confirmed or suspected Detective
3. Influential civilian leaders
4. Players who seem to be organizing civilian strategy

LESS LIKELY TARGETS:
1. Quiet, non-threatening players
2. Players already under suspicion
3. Players who seem confused or unhelpful

Based on recent discussions and events, who do you think is most at risk?
"""

        analysis = self.make_decision(prompt)
        self.add_memory(f"Threat analysis: {analysis}")
        return analysis

    def decide_role_revelation(self) -> Dict:
        """Decide whether to reveal doctor role"""
        context = self.get_context_message()

        prompt = f"""
DOCTOR REVELATION DECISION

Consider revealing your role if:
1. You're about to be voted out and are innocent
2. You've made crucial saves that prove your role
3. The Detective has revealed and needs protection
4. Civilians are losing and need coordination

Consider staying hidden if:
1. Mafia doesn't know who you are yet
2. You're not under immediate threat
3. Your protections haven't been obvious

Should you reveal your role? Return: REVEAL or STAY_HIDDEN
"""

        decision = self.make_decision(prompt)
        decision = decision.strip().upper()

        if decision not in ["REVEAL", "STAY_HIDDEN"]:
            decision = "STAY_HIDDEN"

        return {"decision": decision}

    def reveal_doctor_role(self, reason: str) -> str:
        """Reveal that you are the doctor"""
        prompt = f"""
Time to reveal you're the Doctor!

REASON FOR REVELATION: {reason}

PROTECTIONS MADE: {', '.join(self.protection_history)}

Announce your role convincingly:
1. State you're the Doctor
2. Mention any successful saves (if applicable)
3. Rally civilians to trust you
4. Ask for protection from other civilians

Be dramatic but credible. Keep under 150 words.
"""

        revelation = self.make_decision(prompt)
        self.revealed_role = True
        self.send_message_to_game(revelation)
        self.add_memory("Revealed my doctor role to everyone")
        return revelation

    def support_detective_revelation(
        self, detective_name: str, detective_findings: str
    ) -> str:
        """Support a revealed detective"""
        prompt = f"""
{detective_name} has revealed as Detective with findings: {detective_findings}

As the Doctor, you should:
1. Publicly support the detective
2. Confirm their findings make sense
3. Rally civilians to follow detective's lead
4. Possibly hint at your protective role

Support the detective without fully revealing yourself unless necessary.
"""

        support = self.make_decision(prompt)
        self.send_message_to_game(support)
        return support

    def cast_vote(self, eligible_players: List[str]) -> str:
        """Cast vote to protect civilians and eliminate mafia"""
        context = self.get_context_message()

        prompt = f"""
DOCTOR VOTING DECISION

As the Doctor, vote to:
1. Eliminate confirmed/suspected mafia
2. Protect valuable civilian players
3. Support detective findings (if revealed)
4. Follow logical civilian consensus

ELIGIBLE PLAYERS: {', '.join(eligible_players)}

SUSPECTED ROLES: {', '.join([f"{p}:{r}" for p, r in self.suspected_roles.items()])}

Your goal is protecting innocent lives. Who should be eliminated?
Return ONLY the name.
"""

        vote = self.make_decision(prompt, eligible_players)
        vote = vote.strip().strip('"').strip("'")

        if vote not in eligible_players:
            vote = eligible_players[0] if eligible_players else ""

        self.add_memory(f"Voted to eliminate {vote}")
        return vote

    def participate_in_discussion(
        self, topic: str, previous_messages: List[Dict], discussion_context: str = ""
    ) -> str:
        """Participate in discussion with doctor perspective"""
        context = self.get_context_message()

        msg_history = "\n".join(
            [f"{msg['sender']}: {msg['message']}" for msg in previous_messages[-8:]]
        )

        prompt = f"""
{discussion_context}

DISCUSSION: {topic}

RECENT CONVERSATION:
{msg_history}

YOUR PROTECTION HISTORY:
- Recently protected: {', '.join(self.recent_protections[-3:])}
- Protection strategy: {self.protection_strategy}

As a doctor, contribute to finding mafia:
1. Share observations about suspicious behavior
2. Ask questions to help identify threats
3. Support logical arguments from trusted players
4. Be especially protective of players you've saved
5. Help organize civilian strategy

Be careful not to reveal your role. Act like a concerned civilian.
"""

        response = self.make_decision(prompt)
        self.send_message_to_game(response)
        return response

    def assess_player_role(self, player: str, behavior: str) -> str:
        """Assess what role another player might have"""
        prompt = f"""
ROLE ASSESSMENT: {player}

Their behavior: {behavior}

Based on their actions, voting, and discussion style, what role might they have?
- DETECTIVE: Analytical, asks probing questions, makes logical accusations
- DOCTOR: Protective, concerned about innocent players, helpful
- CIVILIAN: Varies, but generally trying to find mafia
- MAFIA: Deflective, inconsistent, protects other mafia

What role do you suspect {player} has? Return: DETECTIVE, DOCTOR, CIVILIAN, or MAFIA
"""

        assessment = self.make_decision(prompt)
        assessment = assessment.strip().upper()

        if assessment in ["DETECTIVE", "DOCTOR", "CIVILIAN", "MAFIA"]:
            self.suspected_roles[player] = assessment

            if assessment in ["DETECTIVE", "DOCTOR", "CIVILIAN"]:
                self.valuable_civilians.add(player)

        return assessment
