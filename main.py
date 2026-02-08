from fastapi import FastAPI, Request, Depends, Form,responses
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
import dependecies.auth as auth
from datetime import timedelta
from starlette.exceptions import HTTPException as StarletteHTTPException
from database import DB_main as dbm
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
                      register_username: str = Form(...),
                      register_password: str = Form(...),
                      register_confirm_password: str = Form(...),
                      register_email: EmailStr | None =Form(None)):
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
def account(request:Request, user :str = Depends(auth.get_current_user)):
    #print(type(user), user, "user in account")
    username = user.username
    #print(f"username: {username}")
    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={"username": username,
                 "email": user.email,
                 "games": dbm.select_games_by_user(username),
                 "wins": "wins here",
                 "mean_game_time": "mean game time here"}
    )

@app.post("/token")
async def login_for_access_token(request:Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth.authenticate_user(form_data.username, form_data.password)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"value": "Niepoprawne dane logowania"}
        )
    access_token = auth.create_access_token(data={"sub": form_data.username})
    response = responses.RedirectResponse(url="/account", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax", max_age=timedelta(seconds=30))
    print(access_token, "returning token")
    return response

@app.get("/logout")
def logout(request: Request):
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