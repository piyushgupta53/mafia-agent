from typing import Dict, List, Optional, Set
import json
from datetime import datetime
from enum import Enum

class GamePhase(Enum):
    SETUP = "setup"
    FIRST_NIGHT = "first_night"
    DAY = "day"
    NIGHT = "night"
    GAME_OVER = "game_over"

class PlayerStatus(Enum):
    ALIVE = "alive"
    ELIMINATED = "eliminated"
    PROTECTED = "protected"

class GameState:
    def __init__(self):
        self.phase = GamePhase.SETUP
        self.day_count = 0
        self.players: Dict[str, Dict] = {}
        self.mafia_members: Set[str] = set()
        self.alive_players: Set[str] = set()
        self.eliminated_players: Set[str] = set()
        self.votes: Dict[str, str] = {}  # voter -> target
        self.night_actions: Dict[str, Dict] = {}
        self.chat_history: List[Dict] = []
        self.game_log: List[Dict] = []
        self.last_elimination: Optional[str] = None
        self.last_investigation: Optional[Dict] = None
        self.protected_player: Optional[str] = None
        
    def add_player(self, name: str, role: str, agent_instance):
        """Add a player to the game"""
        self.players[name] = {
            "role": role,
            "status": PlayerStatus.ALIVE,
            "agent": agent_instance,
            "votes_received": 0,
            "nights_survived": 0
        }
        self.alive_players.add(name)
        
        if role == "mafia":
            self.mafia_members.add(name)
    
    def eliminate_player(self, player_name: str):
        """Eliminate a player from the game"""
        if player_name in self.alive_players:
            self.alive_players.remove(player_name)
            self.eliminated_players.add(player_name)
            self.players[player_name]["status"] = PlayerStatus.ELIMINATED
            self.last_elimination = player_name
            
            self.log_event({
                "type": "elimination",
                "player": player_name,
                "role": self.players[player_name]["role"],
                "phase": self.phase.value,
                "day": self.day_count
            })
    
    def add_vote(self, voter: str, target: str):
        """Record a vote"""
        self.votes[voter] = target
        if target in self.players:
            self.players[target]["votes_received"] += 1
    
    def clear_votes(self):
        """Clear all votes"""
        self.votes.clear()
        for player in self.players:
            self.players[player]["votes_received"] = 0
    
    def add_night_action(self, player: str, action_type: str, target: Optional[str] = None):
        """Record a night action"""
        self.night_actions[player] = {
            "action": action_type,
            "target": target,
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_night_actions(self):
        """Clear all night actions"""
        self.night_actions.clear()
        self.protected_player = None
    
    def add_chat_message(self, sender: str, message: str, chat_type: str = "public", targets: List[str] = None):
        """Add a chat message to history"""
        chat_entry = {
            "sender": sender,
            "message": message,
            "chat_type": chat_type,
            "targets": targets or [],
            "timestamp": datetime.now().isoformat(),
            "phase": self.phase.value,
            "day": self.day_count
        }
        self.chat_history.append(chat_entry)
        return chat_entry
    
    def log_event(self, event: Dict):
        """Log a game event"""
        event["timestamp"] = datetime.now().isoformat()
        self.game_log.append(event)
    
    def get_vote_counts(self) -> Dict[str, int]:
        """Get current vote counts"""
        vote_counts = {}
        for target in self.votes.values():
            vote_counts[target] = vote_counts.get(target, 0) + 1
        return vote_counts
    
    def get_majority_vote_target(self) -> Optional[str]:
        """Get the player with majority votes"""
        vote_counts = self.get_vote_counts()
        if not vote_counts:
            return None
        
        max_votes = max(vote_counts.values())
        majority_threshold = len(self.alive_players) // 2 + 1
        
        if max_votes >= majority_threshold:
            # Find player with max votes
            for player, votes in vote_counts.items():
                if votes == max_votes:
                    return player
        return None
    
    def check_win_condition(self) -> Optional[str]:
        """Check if the game has ended"""
        alive_mafia = len([p for p in self.alive_players if p in self.mafia_members])
        alive_civilians = len(self.alive_players) - alive_mafia
        
        if alive_mafia == 0:
            return "civilians"
        elif alive_mafia >= alive_civilians:
            return "mafia"
        
        return None
    
    def get_game_stats(self) -> Dict:
        """Get current game statistics"""
        alive_mafia = [p for p in self.alive_players if p in self.mafia_members]
        alive_civilians = [p for p in self.alive_players if p not in self.mafia_members]
        
        return {
            "phase": self.phase.value,
            "day_count": self.day_count,
            "total_alive": len(self.alive_players),
            "alive_mafia": len(alive_mafia),
            "alive_civilians": len(alive_civilians),
            "eliminated_count": len(self.eliminated_players),
            "mafia_members": list(self.mafia_members),
            "alive_players": list(self.alive_players),
            "eliminated_players": list(self.eliminated_players),
            "vote_counts": self.get_vote_counts(),
            "last_elimination": self.last_elimination,
            "winner": self.check_win_condition()
        }
    
    def to_dict(self) -> Dict:
        """Convert game state to dictionary for serialization"""
        return {
            "phase": self.phase.value,
            "day_count": self.day_count,
            "players": {name: {
                "role": info["role"],
                "status": info["status"].value,
                "votes_received": info["votes_received"],
                "nights_survived": info["nights_survived"]
            } for name, info in self.players.items()},
            "mafia_members": list(self.mafia_members),
            "alive_players": list(self.alive_players),
            "eliminated_players": list(self.eliminated_players),
            "votes": self.votes,
            "stats": self.get_game_stats(),
            "chat_history": self.chat_history[-50:],  # Last 50 messages
            "recent_events": self.game_log[-10:]  # Last 10 events
        }