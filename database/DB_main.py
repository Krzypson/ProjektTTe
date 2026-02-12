from pydantic import EmailStr
from sqlmodel import Session, select, func
from database.database import engine, create_db_and_tables
from database.models import Users, Games, GameUsers

def add_user(username: str, password: str, email: EmailStr = None):
    with Session(engine) as session:
        user = Users(username=username, password=password, email=email)
        session.add(user)
        session.commit()
    return "user added"

def add_game(game_id: int, game_time: int, player_count: int):
    with Session(engine) as session:
        game = Games(id=game_id, game_time=game_time, player_count=player_count)
        session.add(game)
    return "game added"

def select_user_info(username: str):
    with Session(engine) as session:
        statement = select(Users).where(Users.username == username)
        result = session.exec(statement).first()
    return result

def select_game_count_by_username(username: str):
    with Session(engine) as session:
        statement = select(func.count(GameUsers.game_id)).where(GameUsers.user_id == username)
        results = session.exec(statement).first()
        return results

def select_won_games_count_by_username(username: str):
    with Session(engine) as session:
        statement = select(func.count(GameUsers.game_id)).where(GameUsers.user_id == username, GameUsers.winner == True)
        results = session.exec(statement).first()
        return results

def select_mean_game_time_by_username(username: str):
    with Session(engine) as session:
        statement = select(func.avg(Games.game_time)).select_from(Games).join(GameUsers, Games.id == GameUsers.game_id).where(GameUsers.user_id == username)
        results = session.exec(statement).first()
        return results

create_db_and_tables()
