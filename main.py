import uvicorn
from fastapi import FastAPI, Request, HTTPException, status, Path, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
# from data import posts
from fastapi.middleware.cors import CORSMiddleware
from schemas import PostCreate, PostResponse, PostsResponse, UserCreate, UserResponse
from typing import Annotated
from sqlalchemy import select, func
from sqlalchemy.orm import Session
import models
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()



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

@app.get("/" , include_in_schema=False, name="home") #include_in_schema will not allow this to be available in routes pages means schema
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db=Annotated[Session, Depends(get_db)]): #fast api consider the function name as route name and as both are connected to the same function
  # return {"message": 'hello World'}
  # return f"<h1>{posts[0]['title']}</h1>"
  result = db.execute(select(models.Post))
  posts = result.scalars().all()
  return templates.TemplateResponse(request,"home.html", {
    "posts": posts,
    "title": "home"
  })

# Users
@app.post("/api/users",
          response_model=UserResponse,
          status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
  username_lower = user.username.strip().lower()
  result = db.execute(
    select(models.User).where(func.lower(models.User.username) == username_lower)
  )
  existing_user = result.scalars().first()
  if existing_user:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Username already exists"
    )
  email_lower = user.email.strip().lower()
  result = db.execute(
    select(models.User).where(func.lower(models.User.email) == email_lower)
  )
  existing_email = result.scalars().first()
  if existing_email:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Email already exists"
    )
  new_user = models.User(
    username = user.username.strip(),
    email = user.email.strip().lower()
  )
  db.add(new_user)
  db.commit()
  db.refresh(new_user)
  return new_user

@app.get("/api/users", response_model=list[UserResponse])
async def get_users(db: Annotated[Session, Depends(get_db)]):
  result = db.execute(select(models.User))
  users = result.scalars().all()
  if not users:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail = "Users not found"
    )
  return users

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int,db: Annotated[Session, Depends(get_db)]):
  result = db.execute(select(models.User).where(models.id == user_id))
  user = result.scalars().first()
  if user:
    return user
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="USer not found")

# get user posts
@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
  result = db.execute(select(models.User).where(models.User.id) == user_id)
  user = result.scalars().first()
  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="USer not found"
    )
  result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
  posts = result.scalars().first()
  return posts

@app.get('/api/posts', response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
  result = db.execute(select(models.Post))
  posts = result.scalars().all()
  return posts


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
   result = db.execute(select(models.User).where(models.User.id == post.user_id))
   user = result.scalars().first()
   if not user:
     raise HTTPException(
       status_code=status.HTTP_404_NOT_FOUND,
       detail="USer not found"
     )
   new_post = models.Post(
     title = post.title,
     content = post.title,
     user_id = post.user_id
   )
   db.add(new_post)
   db.commit()
   db.refresh(new_post)
   return new_post


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
  result = db.execute(select(models.Post).where(models.Post.id == post_id))
  post = result.scalars().first()
  if not post:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
  return post
  

# @app.get('/hello/{name}/{age}') #/{name}/{age} pass it for path aprams
# async def hello(*,name:str= Path(...,min_length=3, max_length=20), age:int=Path(...,gt=1,lt=100)):
#     return {"name": name, "age":age}

# @app.put("/api/posts/{post_id}")
# def get_post(post_id: int, updated_post: posts):
#   for post in posts:
#     if post.get("id") == post_id:
#       post.update(updated_post.dict())
#       return post
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found")


@app.exception_handler(StarletteHTTPException)
async def general_exception_handler(request:Request, exception: StarletteHTTPException):
  if isinstance(exception, HTTPException):
    return JSONResponse(
      status_code=exception.status_code,
      content={
        "status_code":f'{exception.status_code}',
        "message": exception.detail}
    )
  return JSONResponse(
     status_code=exception.status_code,
      content={
        "status_code":f'{exception.status_code}',
        "message": exception.detail}
     )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
   if request.url.path.startswith("/api"):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
        "status_code":f'{status.HTTP_422_UNPROCESSABLE_CONTENT}',
        "message": exception.errors()}
    )


if __name__ == '__main__':
   uvicorn.run("main:app", host='127.0.0.1', port=8000, reload=True)