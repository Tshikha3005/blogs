import asyncio
import datetime
import os
import random
import httpx

# Bring in your configuration assets cleanly
from config import settings
from databsase_async import engine, Base
from main import app  # Bring app instance in directly to fix the Pydantic Settings bug

# ---------------------------------------------------------
# DATA POOL SEEDING
# ---------------------------------------------------------
USERS = [
    {"username": "coreyms", "email": "corey@test.com", "password": "password123", "image": "user1.jpg"},
    {"username": "jdoe", "email": "jdoe@test.com", "password": "password123", "image": "user2.jpg"},
    {"username": "smithe", "email": "smithe@test.com", "password": "password123", "image": "user3.jpg"},
    {"username": "bwilson", "email": "bwilson@test.com", "password": "password123", "image": "user4.jpg"},
    {"username": "mjones", "email": "mjones@test.com", "password": "password123", "image": "user5.jpg"},
    {"username": "aalexander", "email": "aalexander@test.com", "password": "password123", "image": "user6.jpg"}
]

SAMPLE_POSTS = [
    {"title": "Getting Started with FastAPI", "content": "FastAPI is modern, fast, and highly performant framework for building APIs with Python..."},
    {"title": "Understanding Async in Python", "content": "Asyncio can be tricky at first, but once it clicks, it completely changes how you think about I/O bound tasks..."},
    {"title": "SQLAlchemy Relationship Guide", "content": "Defining models, foreign keys, and back-references correctly makes database handling seamless..."},
    {"title": "Pydantic v2 Features", "content": "The new version of Pydantic is incredibly fast because its core validation engine is written in Rust..."},
    {"title": "Deploying Your First Web App", "content": "From local development server to a production VPS, here is a complete checklist..."},
    {"title": "Mastering Git Workflow", "content": "Learn how to use rebase, cherry-pick, and handle complex merge conflicts like a pro..."},
    {"title": "Dockerizing a Python API", "content": "Containerizing your applications ensures consistent behavior across development and production environments..."},
    {"title": "Working with Environment Variables", "content": "Never hardcode secrets. Use python-dotenv or Pydantic BaseSettings to secure configuration data..."},
    {"title": "The Importance of API Pagination", "content": "Returning thousands of database entries at once kills performance. Use skip and limit parameter defaults..."},
    {"title": "Background Tasks vs Celery", "content": "FastAPI's built-in BackgroundTasks are great for quick emails, but use Celery for heavy processing tasks..."}
]

# ---------------------------------------------------------
# REPAIRED DATABASE & TIMELINE HELPERS
# ---------------------------------------------------------
async def clear_existing_data():
    """Wipes your schema completely utilizing AsyncConnection methods safely."""
    print("Clearing existing database tables asynchronously...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def update_post_dates():
    """Updates your timeline records back over several months."""
    print("\nSpreading post timelines out over the past few months...")
    async with engine.begin() as conn:
        posts_table = Base.metadata.tables["posts"]
        result = await conn.execute(posts_table.select())
        posts = result.fetchall()
        
        now = datetime.datetime.now(datetime.timezone.utc)
        for i, post in enumerate(posts):
            days_ago = (len(posts) - i) * 2 + random.randint(0, 2)
            hours_ago = random.randint(1, 23)
            adjusted_date = now - datetime.timedelta(days=days_ago, hours=hours_ago)
            
            await conn.execute(
                posts_table.update()
                .where(posts_table.c.id == post.id)
                .values(date_posted=adjusted_date)
            )

# ---------------------------------------------------------
# REPAIRED ROUTINE
# ---------------------------------------------------------
async def populate() -> None:
    transport = httpx.ASGITransport(app=app)
    
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
        # 1. Async drop & build
        await clear_existing_data()
        
        print(f"\nCreating {len(USERS)} profiles...")
        tokens = []
        
        # 2. Loop through users and target your valid routes
        for user_data in USERS:
            # Match user registration endpoint route prefix config
            user_response = await client.post(
                "/api/users",  # Adjust to "/api/users" if your main.py uses an api prefix!
                json={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                },
            )
            user_response.raise_for_status()
            
            # FIXED: Targets your exact `OAuth2PasswordRequestForm` route endpoint `/token`
            # using 'data=' form content submission layout
            login_resp = await client.post(
                "/api/users/token",  # Adjust to "/token" if included directly on the root app
                data={"username": user_data["email"], "password": user_data["password"]}
            )
            login_resp.raise_for_status()
            token = login_resp.json()["access_token"]
            tokens.append(token)
            
            # Handle profile image binary if setup directory exists
            image_path = os.path.join("populate_images", user_data["image"])
            if os.path.exists(image_path):
                headers = {"Authorization": f"Bearer {token}"}
                with open(image_path, "rb") as f:
                    await client.patch(
                        f"/api/users/{user_response.json()['id']}/picture", 
                        headers=headers, 
                        files={"file": f}
                    )

        print(f"\nGenerating 44 sample blog posts across profiles...")
        # 3. Create posts sequentially matching your post routing design
        for i in range(44):
            token = tokens[i % len(tokens)]
            headers = {"Authorization": f"Bearer {token}"}
            sample = SAMPLE_POSTS[i % len(SAMPLE_POSTS)]
            
            response = await client.post(
                "/api/posts",  # Adjust to "/api/posts" if prefixed in main app initialization
                headers=headers,
                json={
                    "title": f"{sample['title']} (Sample #{i+1})",
                    "content": f"{sample['content']}"
                }
            )
            response.raise_for_status()

        # 4. Finalize timestamps
        await update_post_dates()
        await engine.dispose()
        print("\nDatabase seeded with mock posts and timelines successfully!")

if __name__ == "__main__":
    asyncio.run(populate())