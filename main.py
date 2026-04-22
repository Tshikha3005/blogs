from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from data import posts
from fastapi.middleware.cors import CORSMiddleware
from schemas import PostCreate, PostResponse, PostsResponse

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],      # or ["*"] for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/" , include_in_schema=False, name="home") #include_in_schema will not allow this to be available in routes pages means schema
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request): #fast api consider the function name as route name and as both are connected to the same function
  # return {"message": 'hello World'}
  # return f"<h1>{posts[0]['title']}</h1>"
  return templates.TemplateResponse(request,"home.html", {
    "posts": posts,
    "title": "home"
  })

@app.get('/api/posts', response_model=PostsResponse)
def get_posts():
  return {"data": posts}


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate):
   new_id = max(p['id'] for p in posts) + 1 if posts else 1
   new_post = {
      "id": new_id,
      "author": post.author,
      "content": post.content,
      "title": post.title,
      "date_posted": "April 22, 2026"
   }
   posts.append(new_post)
   return new_post


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
  for post in posts:
    if post.get("id") == post_id:
      return post
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found")
  
# @app.put("/api/posts/{post_id}")
# def get_post(post_id: int, updated_post: posts):
#   for post in posts:
#     if post.get("id") == post_id:
#       post.update(updated_post.dict())
#       return post
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found")

## StarletteHTTPException Handler
@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


### RequestValidationError Handler
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
