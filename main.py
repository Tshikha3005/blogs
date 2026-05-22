import uvicorn
from contextlib import asynccontextmanager
from fastapi.exception_handlers import (
  http_exception_handler,
)
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
# from data import posts
from fastapi.middleware.cors import CORSMiddleware
from databsase_async import Base, engine
from routers import posts, users

@asynccontextmanager
async def lifespan(_app: FastAPI):
  #startup
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
  yield
  #shutdown
  await engine.dispose()

app = FastAPI(lifespan=lifespan)



app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],      # or ["*"] for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name="media")
templates = Jinja2Templates(directory="templates")

# tags: Organizes your /docs (Swagger UI) page into clean, collapsible sections 
# Opens in a new window. Setting tags=["users"] groups all those specific routes together visually under a "users" header 
# Opens in a new window.
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])

@app.exception_handler(StarletteHTTPException)
async def general_exception_handler(request:Request, exception: StarletteHTTPException):
  if isinstance(exception, HTTPException):
    return await http_exception_handler(request, exception)
  return await http_exception_handler(request, exception)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
   if request.url.path.startswith("/api"):
    return await http_exception_handler(request, exception)


if __name__ == '__main__':
   uvicorn.run("main:app", host='127.0.0.1', port=8000, reload=True)