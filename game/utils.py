"""
Utility functions for the Mafia game
"""
import random
import time
from typing import List, Dict, Any
from datetime import datetime

def generate_player_names(count: int) -> List[str]:
    """Generate unique player names"""
    names = [
        "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", 
        "Grace", "Henry", "Iris", "Jack", "Kate", "Liam", 
        "Maya", "Noah", "Olivia", "Paul", "Quinn", "Ruby", 
        "Sam", "Tara", "Uma", "Victor", "Wendy", "Xander", 
        "Yara", "Zoe"
    ]
    
    if count > len(names):
        # Generate additional names if needed
        additional = [f"Player{i}" for i in range(len(names) + 1, count + 1)]
        names.extend(additional)
    
    random.shuffle(names)
    return names[:count]

def assign_roles(player_count: int, mafia_count: int, detective_count: int, doctor_count: int) -> List[str]:
    """Assign roles to players randomly"""
    civilian_count = player_count - mafia_count - detective_count - doctor_count
    
    if civilian_count < 0:
        raise ValueError("Too many special roles for the number of players")
    
    roles = (["mafia"] * mafia_count + 
             ["detective"] * detective_count + 
             ["doctor"] * doctor_count + 
             ["civilian"] * civilian_count)
    
    random.shuffle(roles)
    return roles

def calculate_game_balance(total_players: int, mafia_count: int) -> Dict[str, Any]:
    """Calculate if the game setup is balanced"""
    civilian_count = total_players - mafia_count
    
    # Basic balance check: mafia should be 20-30% of total players
    mafia_percentage = (mafia_count / total_players) * 100
    
    balance_info = {
        "total_players": total_players,
        "mafia_count": mafia_count,
        "civilian_count": civilian_count,
        "mafia_percentage": mafia_percentage,
        "is_balanced": 20 <= mafia_percentage <= 30,
        "recommended_mafia": max(1, round(total_players * 0.25)),
        "balance_rating": "good" if 20 <= mafia_percentage <= 30 else "poor"
    }
    
    return balance_info

def format_time_elapsed(start_time: datetime) -> str:
    """Format elapsed time since start"""
    elapsed = datetime.now() - start_time
    total_seconds = int(elapsed.total_seconds())
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def sanitize_message(message: str) -> str:
    """Sanitize chat messages for display"""
    # Remove any potentially harmful content
    message = message.replace('<script>', '').replace('</script>', '')
    message = message.replace('<iframe>', '').replace('</iframe>', '')
    
    # Limit message length
    if len(message) > 500:
        message = message[:497] + "..."
    
    return message

def calculate_suspicion_score(voting_history: List[Dict], target_player: str) -> float:
    """Calculate a suspicion score based on voting patterns"""
    if not voting_history:
        return 5.0  # Neutral score
    
    score = 5.0  # Start with neutral
    vote_count = 0
    
    for vote_round in voting_history:
        votes = vote_round.get('votes', {})
        
        # Check who voted for this player
        votes_against = sum(1 for vote in votes.values() if vote == target_player)
        total_votes = len(votes)
        
        if total_votes > 0:
            vote_percentage = votes_against / total_votes
            # Higher percentage of votes = higher suspicion
            score += vote_percentage * 2
            vote_count += 1
    
    # Normalize score and clamp to 1-10
    if vote_count > 0:
        score = min(10, max(1, score))
    
    return round(score, 1)

def get_game_phase_emoji(phase: str) -> str:
    """Get emoji representation for game phases"""
    phase_emojis = {
        "setup": "⚙️",
        "first_night": "🌙",
        "night": "🌙",
        "day": "☀️",
        "voting": "🗳️",
        "game_over": "🏁"
    }
    return phase_emojis.get(phase, "🎮")

def generate_personality_traits() -> Dict[str, str]:
    """Generate random personality traits for agents"""
    traits = {
        "communication_style": random.choice([
            "analytical and logical",
            "emotional and persuasive", 
            "quiet and observant",
            "aggressive and confrontational",
            "diplomatic and measured"
        ]),
        "suspicion_level": random.choice([
            "highly suspicious of everyone",
            "trusting but cautious",
            "paranoid and defensive",
            "logical and evidence-based"
        ]),
        "strategy_preference": random.choice([
            "prefers direct accusations",
            "likes to build alliances",
            "focuses on behavioral analysis",
            "follows group consensus",
            "contrarian and independent"
        ])
    }
    return traits

def validate_game_config(config: Dict) -> List[str]:
    """Validate game configuration and return any errors"""
    errors = []
    
    total_players = config.get("total_players", 0)
    mafia_count = config.get("mafia_count", 0)
    detective_count = config.get("detective_count", 0)
    doctor_count = config.get("doctor_count", 0)
    
    if total_players < 5:
        errors.append("Minimum 5 players required")
    
    if total_players > 25:
        errors.append("Maximum 25 players allowed")
    
    special_roles = mafia_count + detective_count + doctor_count
    if special_roles >= total_players:
        errors.append("Too many special roles for player count")
    
    if mafia_count < 1:
        errors.append("At least 1 mafia member required")
    
    if mafia_count >= total_players / 2:
        errors.append("Mafia cannot be 50% or more of players")
    
    return errors

def create_game_summary(game_state) -> Dict[str, Any]:
    """Create a comprehensive game summary"""
    stats = game_state.get_game_stats()
    
    summary = {
        "game_duration": f"{stats['day_count']} days",
        "total_messages": len(game_state.chat_history),
        "total_eliminations": stats['eliminated_count'],
        "winner": stats.get('winner', 'ongoing'),
        "final_survivor_count": stats['total_alive'],
        "mafia_members": list(game_state.mafia_members),
        "key_events": game_state.game_log[-10:],  # Last 10 events
        "longest_day": "N/A",  # Could be calculated from logs
        "most_suspicious_player": "N/A",  # Could be calculated from voting
        "most_trusted_player": "N/A"  # Could be calculated from voting
    }
    
    return summary

def debug_game_state(game_state, detailed: bool = False) -> str:
    """Generate debug information about current game state"""
    debug_info = []
    
    debug_info.append(f"=== GAME STATE DEBUG ===")
    debug_info.append(f"Phase: {game_state.phase.value}")
    debug_info.append(f"Day: {game_state.day_count}")
    debug_info.append(f"Alive Players: {len(game_state.alive_players)}")
    debug_info.append(f"Eliminated Players: {len(game_state.eliminated_players)}")
    debug_info.append(f"Mafia Members: {len(game_state.mafia_members)}")
    
    if detailed:
        debug_info.append(f"\nDETAILED INFO:")
        debug_info.append(f"Alive: {', '.join(game_state.alive_players)}")
        debug_info.append(f"Eliminated: {', '.join(game_state.eliminated_players)}")
        debug_info.append(f"Current Votes: {game_state.votes}")
        debug_info.append(f"Night Actions: {len(game_state.night_actions)}")
        debug_info.append(f"Chat Messages: {len(game_state.chat_history)}")
    
    debug_info.append("=" * 25)
    
    return "\n".join(debug_info)

class GameTimer:
    """Simple timer for game phases"""
    
    def __init__(self):
        self.start_time = None
        self.phase_start = None
    
    def start_game(self):
        """Start the overall game timer"""
        self.start_time = datetime.now()
        self.phase_start = self.start_time
    
    def start_phase(self):
        """Start a new phase timer"""
        self.phase_start = datetime.now()
    
    def get_game_duration(self) -> str:
        """Get total game duration"""
        if not self.start_time:
            return "0s"
        return format_time_elapsed(self.start_time)
    
    def get_phase_duration(self) -> str:
        """Get current phase duration"""
        if not self.phase_start:
            return "0s"
        return format_time_elapsed(self.phase_start)

def log_error(error: Exception, context: str = ""):
    """Log errors with context"""
    timestamp = datetime.now().isoformat()
    error_msg = f"[{timestamp}] ERROR in {context}: {str(error)}"
    print(error_msg)
    # In a production environment, you might want to log to a file
    return error_msg