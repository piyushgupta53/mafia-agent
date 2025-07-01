from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import asyncio
import threading
import sys
import os

# Add parent directory to path to import game modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.game_controller import MafiaGameController
from config import FLASK_CONFIG, AGENT_COLORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mafia_game_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global game controller
game_controller = None
game_thread = None

def frontend_callback(event_type: str, data):
    """Callback function to send updates to frontend"""
    socketio.emit('game_update', {
        'type': event_type,
        'data': data
    })

@app.route('/')
def index():
    """Main game interface"""
    return render_template('index.html', agent_colors=AGENT_COLORS)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('start_game')
def handle_start_game():
    """Handle game start request"""
    global game_controller, game_thread
    
    print("Starting new game...")
    
    # Stop existing game if running
    if game_controller and game_controller.game_running:
        game_controller.game_running = False
        if game_thread:
            game_thread.join(timeout=5)
    
    # Create new game controller
    game_controller = MafiaGameController(frontend_callback)
    
    # Start game in separate thread
    def run_game():
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the game
            loop.run_until_complete(game_controller.start_game())
            loop.close()
            
        except Exception as e:
            print(f"Error in game thread: {e}")
            socketio.emit('error', {'message': f'Game error: {str(e)}'})
    
    game_thread = threading.Thread(target=run_game)
    game_thread.daemon = True
    game_thread.start()
    
    emit('game_started', {'message': 'Game starting...'})

@socketio.on('stop_game')
def handle_stop_game():
    """Handle game stop request"""
    global game_controller, game_thread
    
    if game_controller:
        game_controller.game_running = False
        print("Game stopped by user")
        emit('game_stopped', {'message': 'Game stopped'})

@socketio.on('get_game_state')
def handle_get_game_state():
    """Handle request for current game state"""
    if game_controller and game_controller.game_state:
        emit('game_state', game_controller.game_state.to_dict())
    else:
        emit('game_state', {'message': 'No active game'})

@socketio.on('request_stats')
def handle_request_stats():
    """Handle request for game statistics"""
    if game_controller and game_controller.game_state:
        stats = game_controller.game_state.get_game_stats()
        emit('game_stats', stats)

if __name__ == '__main__':
    print(f"Starting Mafia Game Server on {FLASK_CONFIG['host']}:{FLASK_CONFIG['port']}")
    socketio.run(
        app, 
        host=FLASK_CONFIG['host'], 
        port=FLASK_CONFIG['port'], 
        debug=FLASK_CONFIG['debug']
    )