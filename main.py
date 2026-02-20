from fastapi import FastAPI, Request, Depends, Form, responses, WebSocket, WebSocketDisconnect, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
import auth.auth as auth
from datetime import timedelta, datetime
from starlette.exceptions import HTTPException as StarletteHTTPException
from database import DB_main as dbm
from game.websocket_handlers import manager

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"value": "",
                 "username": ""}
    )

@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"register_response": ""}
    )

@app.post("/register")
async def create_user(request: Request,
                      register_username: str | None = Form(""),
                      register_password: str | None= Form(""),
                      register_confirm_password: str | None = Form(""),
                      register_email: EmailStr | None = Form(None)):
    if not register_username or not register_password or not register_confirm_password:
        return_value = "username, password and confirm password are required"
    else:
        if register_password != register_confirm_password:
            return_value = "Passwords do not match"
        else:
            return_value = auth.create_user(register_username, register_password, register_email)

    return templates.TemplateResponse(
    request=request,
    name="register.html",
    context={"register_response": return_value}
    )

@app.get("/account", response_class=HTMLResponse)
def account(request:Request, user :str = Depends(auth.get_current_user), game_error: str | None = None):
    username = user.username
    if not game_error:
        game_error = ""
    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={"username": username,
                 "email": user.email,
                 "games": dbm.select_game_count_by_username(username),
                 "wins": dbm.select_won_games_count_by_username(username),
                 "mean_game_time": f"{dbm.select_mean_game_time_by_username(username)} s",
                 "rooms": manager.get_rooms(),
                 "game_error": game_error
                 }
    )

@app.post("/create_room")
async def create_room(input_room_name: str | None = Form(""), input_max_players: int | None = Form("")):
    await manager.create_room(room_id=input_room_name, max_players=input_max_players, track_length=10)
    return RedirectResponse(url=f"/game/{input_room_name}", status_code=302)

@app.post("/token")
async def login_for_access_token(
        request:Request,
        username: str | None = Form(""),
        password: str | None = Form("")):
    wrong_data_response = templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"value": "Incorrect username or password",}
        )
    if not username or not password:
        return wrong_data_response
    user = auth.authenticate_user(username, password)
    if not user:
        return wrong_data_response
    access_token = auth.create_access_token(data={"sub": username})

    token_max_age = int(timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds())
    token_end_time = datetime.now().timestamp() + token_max_age
    print(token_end_time)

    response = responses.RedirectResponse(url="/account", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=token_max_age
    )

    response.set_cookie(
        key="token_expiration",
        value=str(token_end_time),
        httponly=False,
        samesite="lax",
        max_age=token_max_age
    )

    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token")
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    status_code = exc.status_code
    error_templates = {
        401: "401 - Unauthorized.",
        403: "403 - Forbidden.",
        404: "404 - Page not found.",
        500: "500 - Internal Server Error.",
    }
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        status_code=status_code,
        context={"status_code": status_code, "detail": exc.detail, "error_message": error_templates[status_code]}
    )


@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str):
    await manager.connect(websocket, room_id, username)
    try:
        await manager.broadcast_to_room(f" {username} joined the room", room_id)
        players = manager.get_room_players(room_id)
        await manager.broadcast_to_room(f"PLAYERLIST:{','.join(players)}", room_id)
        await manager.broadcast_ready_status(room_id)
        await manager.broadcast_player_positions(room_id)

        while True:
            data = await websocket.receive_text()
            if data == "READY_TOGGLE":
                await manager.toggle_ready(room_id, username)
            elif data == "ROLL_DICE":
                await manager.handle_dice_roll(room_id, username)
            else:
                await manager.broadcast_to_room(f" {username}: {data}", room_id)
    except WebSocketDisconnect:
        manager.disconnect(room_id, username)
        await manager.broadcast_to_room(f" {username} left the room", room_id)
        players = manager.get_room_players(room_id)
        if players:
            await manager.broadcast_to_room(f"PLAYERLIST:{','.join(players)}", room_id)
            await manager.broadcast_ready_status(room_id)
            await manager.broadcast_player_positions(room_id)

@app.get("/game/{room_id}")
def test_game(request: Request, user: str = Depends(auth.get_current_user), room_id: str = Path(...)):
    username = user.username
    print(f"in /game/{room_id}")
    if room_id not in manager.room_config:
        print(f"Room {room_id} not found in config")
        raise StarletteHTTPException(status_code=500, detail="Room not found")
    if len(manager.get_room_players(room_id)) == manager.room_config[room_id]["max_players"]:
        if username not in manager.get_room_players(room_id):
            return RedirectResponse(url=f"/account/?game_error=room is full", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="game.html",
        context={"username": username,
                 "room_id": room_id,
                 "track_length": manager.room_config[room_id]["track_length"]
        }
    )
