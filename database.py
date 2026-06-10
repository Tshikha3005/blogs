import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 1. Load the secrets from the .env file into Python's memory
load_dotenv()

# 2. Grab the variables safely using os.getenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
# 2. Wrap your password with quote_plus to safely encode special characters like @, !, #
safe_password = urllib.parse.quote_plus(DB_PASSWORD)
# asyncmy is for async driver
# 3. Use the safe_password variable here
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# 4. Create the Engine
engine = create_engine(DATABASE_URL)

# 5. Create the session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 6. Create the base class for your tables
class Base(DeclarativeBase):
  pass

def get_db():
  with SessionLocal() as db:
    yield db
