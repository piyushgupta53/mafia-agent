from .base_agent import MafiaBaseAgent
from typing import List, Dict, Optional

class NarratorAgent(MafiaBaseAgent):
    """Narrator agent that facilitates the game and provides updates"""
    
    def __init__(self, name: str, game_state, frontend_callback=None):
        personality = """You are the omniscient game narrator. You facilitate all phases of the game, 
        announce events dramatically, and provide clear instructions. You maintain the game's atmosphere 
        with engaging storytelling while keeping players informed of the current state and rules."""
        
        super().__init__(
            name=name, 
            role="narrator", 
            personality=personality,
            game_state=game_state,
            frontend_callback=frontend_callback
        )
    
    def announce_game_start(self, players: List[str]) -> str:
        """Announce the start of the game"""
        message = f"""
🌙 **THE MAFIA GAME BEGINS** 🌙

Welcome to the village! {len(players)} citizens have gathered, but evil lurks among you...

**PLAYERS:** {', '.join(players)}

**SETUP:**
- 3 Mafia members (know each other, eliminate civilians at night)
- 1 Detective (investigates one player each night)
- 1 Doctor (protects one player each night)
- 7 Civilians (find and vote out the mafia)

Roles have been secretly assigned. The first night begins now!

🌙 **FIRST NIGHT PHASE** 🌙
Everyone goes to sleep... but the mafia awakens to learn their teammates.
"""
        
        self.send_message_to_game(message)
        return message
    
    def announce_phase_transition(self, new_phase: str, day_count: int = 0) -> str:
        """Announce transition to a new game phase"""
        if new_phase == "night":
            message = f"""
🌙 **NIGHT {day_count} BEGINS** 🌙

The village falls asleep... but evil stirs in the darkness.

**NIGHT ACTIONS:**
- Mafia: Choose your target for elimination
- Detective: Choose someone to investigate
- Doctor: Choose someone to protect
- Civilians: Sleep peacefully

Submit your actions. Dawn will come soon...
"""
        elif new_phase == "day":
            message = f"""
☀️ **DAY {day_count} BEGINS** ☀️

The sun rises on the village. What happened in the night?

**DAY PHASE:**
- Discuss what you observed
- Share information and suspicions
- Vote to eliminate a suspected mafia member
- Work together to find the truth

Time for discussion and voting!
"""
        else:
            message = f"**PHASE CHANGE:** {new_phase.upper()}"
        
        self.send_message_to_game(message)
        return message
    
    def announce_night_results(self, eliminated: Optional[str], protected: Optional[str], investigation: Optional[Dict]) -> str:
        """Announce what happened during the night"""
        if eliminated and protected and eliminated == protected:
            # Doctor save
            message = f"""
🏥 **DAWN BREAKS** 🏥

The mafia struck in the night, targeting {eliminated}...
But the Doctor was there! {eliminated} has been SAVED and lives to see another day!

No one was eliminated last night.
"""
        elif eliminated:
            # Someone was eliminated
            message = f"""
💀 **DAWN BRINGS TRAGEDY** 💀

The village awakens to terrible news...
{eliminated} has been found eliminated! They were a loyal member of the community.

The mafia has struck again.
"""
        else:
            # No elimination (first night or other reason)
            message = f"""
🌅 **PEACEFUL DAWN** 🌅

The village awakens peacefully. No one was harmed during the night.

The investigation continues...
"""
        
        self.send_message_to_game(message)
        
        # Send investigation result privately to detective
        if investigation:
            detective_msg = f"🔍 **INVESTIGATION RESULT** 🔍\n{investigation['target']} is a {investigation['result'].upper()}."
            self.send_private_message(investigation['detective'], detective_msg)
        
        return message
    
    def announce_voting_phase(self, eligible_players: List[str]) -> str:
        """Announce the start of voting"""
        message = f"""
🗳️ **VOTING PHASE BEGINS** 🗳️

Time to decide who to eliminate from the village!

**ELIGIBLE PLAYERS:** {', '.join(eligible_players)}

Discuss, accuse, and defend. When ready, cast your votes.
Majority rules - the player with the most votes will be eliminated.

Choose wisely... the fate of the village depends on it!
"""
        
        self.send_message_to_game(message)
        return message
    
    def announce_elimination(self, eliminated_player: str, vote_counts: Dict[str, int]) -> str:
        """Announce the result of voting"""
        role = self.game_state.players[eliminated_player]["role"]
        
        message = f"""
⚖️ **THE VILLAGE HAS DECIDED** ⚖️

{eliminated_player} has been eliminated by majority vote!

**FINAL VOTE COUNTS:**
{chr(10).join([f"- {player}: {votes} votes" for player, votes in sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)])}

{eliminated_player} was a {role.upper()}!

The truth is revealed... but is the village safer?
"""
        
        self.send_message_to_game(message)
        return message
    
    def announce_game_end(self, winner: str, final_stats: Dict) -> str:
        """Announce the end of the game"""
        if winner == "mafia":
            message = f"""
🔴 **MAFIA VICTORY!** 🔴

The mafia has achieved their dark goals!

**SURVIVING MAFIA:** {', '.join([p for p in final_stats['alive_players'] if p in final_stats['mafia_members']])}

**GAME SUMMARY:**
- Days survived: {final_stats['day_count']}
- Total eliminations: {final_stats['eliminated_count']}
- Final survivors: {final_stats['total_alive']}

The village falls to darkness... 😈
"""
        else:
            message = f"""
🟢 **CIVILIAN VICTORY!** 🟢

Justice prevails! All mafia members have been eliminated!

**HEROES OF THE VILLAGE:** {', '.join(final_stats['alive_players'])}

**GAME SUMMARY:**
- Days survived: {final_stats['day_count']}
- Total eliminations: {final_stats['eliminated_count']}
- Mafia eliminated: {len(final_stats['mafia_members'])}

The village is safe once again! 🎉
"""
        
        self.send_message_to_game(message)
        return message
    
    def provide_game_status(self) -> str:
        """Provide current game status"""
        stats = self.game_state.get_game_stats()
        
        message = f"""
📊 **GAME STATUS** 📊

**Phase:** {stats['phase']} (Day {stats['day_count']})
**Players Alive:** {stats['total_alive']}
**Players Eliminated:** {stats['eliminated_count']}

**ALIVE:** {', '.join(stats['alive_players'])}
**ELIMINATED:** {', '.join(stats['eliminated_players']) if stats['eliminated_players'] else 'None'}

The investigation continues...
"""
        
        self.send_message_to_game(message)
        return message
    
    def send_private_message(self, target: str, message: str):
        """Send a private message to a specific player"""
        chat_entry = self.game_state.add_chat_message(
            sender=self.name,
            message=message,
            chat_type="private",
            targets=[target]
        )
        
        if self.frontend_callback:
            self.frontend_callback("new_message", chat_entry)
    
    def facilitate_discussion(self, topic: str, duration: int = 120) -> str:
        """Facilitate a group discussion"""
        message = f"""
💬 **DISCUSSION TIME: {topic}** 💬

You have {duration} seconds to discuss.

Share your thoughts, suspicions, and evidence.
Listen carefully to others and watch for inconsistencies.

The clock is ticking... use your time wisely!
"""
        
        self.send_message_to_game(message)
        return message
    
    def remind_actions(self, pending_players: List[str], action_type: str) -> str:
        """Remind players to submit their actions"""
        message = f"""
⏰ **ACTION REMINDER** ⏰

Waiting for {action_type} from: {', '.join(pending_players)}

Please submit your actions to continue the game!
"""
        
        self.send_message_to_game(message)
        return message