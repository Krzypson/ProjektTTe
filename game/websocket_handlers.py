from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, username: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][username] = websocket

    def disconnect(self, room_id: str, username: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].pop(username)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast_to_room(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id].values():
                await connection.send_text(message)

    async def get_room_players(self, room_id: str) -> list[str]:
        return list(self.active_connections.get(room_id,{}).keys())


manager = ConnectionManager()