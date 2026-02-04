from sqlmodel import SQLModel, Field

class Games(SQLModel, table=True):
    id: int = Field(primary_key=True)
    game_time: int = Field(index=True)
    player_count: int

class Users(SQLModel, table=True):
    username: str = Field(index=True, min_length=4, max_length=32, unique=True, primary_key=True)
    password: str = Field(min_length=4)
    email: str = Field(default= None, unique=True)

class GameUsers(SQLModel, table=True):
    game_id: int = Field(foreign_key="games.id", primary_key=True)
    user_id: str = Field(foreign_key="users.username", primary_key=True)
    winner: bool = Field(default=False)
    #do amazonek
    #teamA: bool = Field(default=False)

#do amazonek
"""class Game_Presets(SQLModel, table=True):
    id: int = Field(primary_key=True)
    players: int
    teamA_size: int
    treasure_count: int
    traps_count: int"""
