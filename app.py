# Flask imports - no monkey patching needed for threading mode
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
import os

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Initialize SocketIO - auto-detect async mode
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

@app.route('/')
def index():
    return jsonify({
        "status": "online", 
        "message": "Secure Text Sync Backend is Running! (Room Support Enabled)"
    })

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_room')
def on_join(data):
    """Allow client to join with strict role separation"""
    room_code = data.get('code')
    device_type = data.get('type')  # 'sender' or 'receiver'
    
    if not room_code or not device_type:
        return

    # 1. Everyone joins the main room for status updates
    join_room(room_code)
    
    # 2. Receivers join a special listening room
    if device_type == 'receiver':
        join_room(f"{room_code}_recv")
        print(f"🔊 Receiver joined room: {room_code}")
    else:
        print(f"📱 Sender joined room: {room_code}")
    
    # Notify others (e.g. tell Senders that a Receiver is online)
    emit('room_joined', {'message': f'{device_type} connected', 'type': device_type}, to=room_code)

@socketio.on('send_text')
def handle_text(data):
    """Send text ONLY to Receivers"""
    room_code = data.get('code')
    text = data.get('text', '')
    
    if room_code and text:
        print(f"Transmission to {room_code}: {text[:20]}...")
        
        # STRICT RULE: Only send to the Receiver sub-room
        # Senders (who are not in this sub-room) will NOT get the message.
        emit('receive_text', data, to=f"{room_code}_recv")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
