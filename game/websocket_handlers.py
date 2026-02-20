from fastapi import WebSocket
import random
from database import DB_main as dbm
import time


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[str, WebSocket]] = {}
        self.room_config: dict[str, dict] = {}
        self.player_ready_status: dict[str, dict[str, bool]] = {}
        self.player_positions: dict[str, dict[str, int]] = {}
        self.current_turn: dict[str, str] = {}

    async def create_room(self, room_id: str, max_players: int = 4, track_length: int = 15):
        self.room_config[room_id] = {"max_players": max_players, "track_length": track_length, "start_time": 0}
        self.player_ready_status[room_id] = {}
        self.player_positions[room_id] = {}

    async def connect(self, websocket: WebSocket, room_id: str, username: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][username] = websocket

        if room_id not in self.player_ready_status:
            self.player_ready_status[room_id] = {}
        self.player_ready_status[room_id][username] = False

        if room_id not in self.player_positions:
            self.player_positions[room_id] = {}
        self.player_positions[room_id][username] = 0

    def disconnect(self, room_id: str, username: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].pop(username, None)
            if room_id in self.player_ready_status:
                self.player_ready_status[room_id].pop(username, None)
            if room_id in self.player_positions:
                self.player_positions[room_id].pop(username, None)

            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
                del self.room_config[room_id]
                if room_id in self.player_ready_status:
                    del self.player_ready_status[room_id]
                if room_id in self.player_positions:
                    del self.player_positions[room_id]

    async def broadcast_to_room(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id].values():
                await connection.send_text(message)

    def get_room_players(self, room_id: str) -> list[str]:
        return list(self.active_connections.get(room_id, {}).keys())

    def get_rooms(self):
        rooms = []
        for connection in self.active_connections.items():
            rooms.append(
                {
                    "room_id": connection[0],
                    "player_count": len(connection[1]),
                    "max_players": int(self.room_config[connection[0]]["max_players"])
                }
            )
        return rooms

    async def toggle_ready(self, room_id: str, username: str):
        if room_id in self.player_ready_status and username in self.player_ready_status[room_id]:
            self.player_ready_status[room_id][username] = not self.player_ready_status[room_id][username]
            await self.broadcast_ready_status(room_id)
            if self.are_all_players_ready(room_id):
                await self.start_game(room_id)

    def are_all_players_ready(self, room_id: str):
        if room_id not in self.player_ready_status:
            return False

        statuses = self.player_ready_status[room_id]
        return len(statuses) > 0 and all(statuses.values())


    async def start_game(self, room_id: str):
        players = self.get_room_players(room_id)
        if players:
            first_player = players[0]
            self.current_turn[room_id] = first_player
            await self.broadcast_to_room(f"GAME_START:{first_player}", room_id)
        for username in self.get_room_players(room_id):
            self.player_positions[room_id][username]=0
        self.room_config[room_id]["start_time"] = time.time()


    async def broadcast_ready_status(self, room_id: str):
        if room_id in self.player_ready_status:
            status_list = [
                f"{username}:{('ready' if ready else 'not_ready')}"
                for username, ready in self.player_ready_status[room_id].items()
            ]
            await self.broadcast_to_room(f"READY_STATUS:{','.join(status_list)}", room_id)

    async def broadcast_player_positions(self, room_id: str):
        if room_id in self.player_positions:
            position_list = [
                f"{username}:{position}"
                for username, position in self.player_positions[room_id].items()
            ]
            await self.broadcast_to_room(f"PLAYER_POSITIONS:{','.join(position_list)}", room_id)

    async def handle_dice_roll(self, room_id: str, username: str):
        if room_id not in self.current_turn or self.current_turn[room_id] != username:
            return
        dice_result = random.randint(1, 6)

        if room_id in self.player_positions and username in self.player_positions[room_id]:
            old_position = self.player_positions[room_id][username]
            new_position = old_position + dice_result
            if new_position < self.room_config[room_id]["track_length"]-1:
                self.player_positions[room_id][username] = new_position
                await self.broadcast_player_positions(room_id)
                await self.next_turn(room_id)
            else:
                await self.win(room_id, username)
                self.player_positions[room_id][username] = self.room_config[room_id]["track_length"]-1
                await self.broadcast_player_positions(room_id)

    async def next_turn(self, room_id: str):
        players = self.get_room_players(room_id)
        if not players or room_id not in self.current_turn:
            return

        current_player = self.current_turn[room_id]
        current_index = players.index(current_player) if current_player in players else -1
        next_index = (current_index + 1) % len(players)
        next_player = players[next_index]

        self.current_turn[room_id] = next_player
        await self.broadcast_to_room(f"TURN_CHANGE:{next_player}", room_id)

    async def add_stats(self, room_id: str, winner: str, game_time: int = 0):
        #print("in stats")
        game_id = time.time_ns()
        dbm.add_game(game_id=game_id, game_time=game_time, player_count=len(self.get_room_players(room_id)))
        for username in self.get_room_players(room_id):
            #print(username)
            if username == winner:
                #print("is winner")
                dbm.add_game_user(game_id=game_id, user_id=username, winner=True)
            else:
                #print("is not winner")
                dbm.add_game_user(game_id=game_id, user_id=username, winner=False)
        await self.broadcast_player_positions(room_id)

    async def win(self, room_id: str, username: str):
        await self.broadcast_to_room(f"WIN:{username}", room_id)
        game_time = time.time() - self.room_config[room_id]["start_time"]
        await self.add_stats(room_id=room_id, winner=username, game_time=game_time)

manager = ConnectionManager()