import uvicorn
from fastapi import FastAPI, HTTPException, status, Request, Path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse #normal JSON responses
# The short answer is: FastAPI’s HTTPException inherits directly from Starlette’s HTTPException but adds extra functionality specifically designed for building web APIs.
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from data import posts
from schemas import PostCreate, PostResponse, PostsResponse


app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins = ['*'],
  allow_credentials = True,
  allow_methods = ['*'],
  allow_headers = ['*']
)

@app.get('/api/posts', response_model=list[PostResponse], status_code=status.HTTP_200_OK)
async def get_posts():
  return posts

@app.get('/api/posts/{post_id}', response_model=PostResponse,status_code=status.HTTP_200_OK)
async def get_post_by_id(post_id: int):
    for post in posts:
      if post.get("id") == post_id:
         return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found")

@app.post('/api/posts',response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate):
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


@app.exception_handler(StarletteHTTPException)
def general_exception_handler(request:Request, exception: StarletteHTTPException):
  if request.url.path.startswith("/api"):
    return JSONResponse(
      status_code=exception.status_code,
      content={
        "status_code":f'{exception.status_code}',
        "message": "OOPs!! Something went wrong"}
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
   if request.url.path.startswith("/api"):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
        "status_code":f'{status.HTTP_422_UNPROCESSABLE_CONTENT}',
        "message": exception.errors()}
    )

# In Python, the variable __name__ is a special built-in variable that tells you the name of the current module. The reason you specifically use "__main__" (and not your filename or variable name) is because of how Python handles script execution.
if __name__ == '__main__':
   uvicorn.run("posts:app", host='127.0.0.1', port=8001, reload=True)