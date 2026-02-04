from sqlmodel import Session, select
from database import engine, create_db_and_tables
from models import Users, Games, GameUsers
from time import time_ns

def add_user(username: str, password: str):
    with Session(engine) as session:
        user = Users(username=username, password=password)
        session.add(user)
        session.commit()

def add_game(game_time: int, usernames: list[str], winners: list[str]):
    with Session(engine) as session:
        game = Games(id= time_ns(), game_time=game_time)
        session.add(game)
        for username in usernames:
            if username in winners:
                game_winner = GameUsers(game_id=game.id, user_id=username, winner=True)
                session.add(
                    game_winner
                )
            else:
                game_user = GameUsers(game_id=game.id, user_id=username)
                session.add(game_user)
        session.commit()

def select_user_info(username: str):
    with Session(engine) as session:
        statement = select(Users).where(Users.username == username)
        result = session.exec(statement).one()
    return()

def select_gameUsers_by_username(username: str):
    with Session(engine) as session:
        statement = select(GameUsers).where(GameUsers.user_id == username)
        results = session.exec(statement)
        return ()

def select_game(id: int):
    with Session(engine) as session:
        statement = select(Games).where(Games.id == id)
        results = session.exec(statement)
        return()

def main():
    create_db_and_tables()

main()
