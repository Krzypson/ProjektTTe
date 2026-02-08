from pydantic import EmailStr
from sqlmodel import Session, select
from database.database import engine, create_db_and_tables
from database.models import Users, Games, GameUsers
from time import time_ns

def add_user(username: str, password: str, email: EmailStr = None):
    with Session(engine) as session:
        user = Users(username=username, password=password, email=email)
        session.add(user)
        session.commit()
    return "user added"

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
        result = session.exec(statement).first()
    return(result)

def select_gameUsers_by_username(username: str):
    with Session(engine) as session:
        statement = select(GameUsers).where(GameUsers.user_id == username)
        results = session.exec(statement)
        return ()

def select_game(game_id: int):
    with Session(engine) as session:
        statement = select(Games).where(Games.id == game_id)
        results = session.exec(statement)
        return()

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

create_db_and_tables()
