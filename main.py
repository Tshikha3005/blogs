from fastapi import FastAPI
from data import posts

app = FastAPI()

@app.get('/')
def home():
  return posts