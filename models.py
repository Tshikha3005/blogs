# This is a beautifully written, modern database configuration using SQLAlchemy 2.0. It sets up a classic One-to-Many relationship: One User can write Many Posts, but each Post belongs to exactly One User.
# Global configuraTION and metadata
# This line allows Python to look ahead at types that haven't been fully defined yet in the script. 
# Notice how inside User, you reference list[Post], even though the Post class isn't created until lower down in the file.
#  This import prevents Python from crashing with a NameError.
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
  email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
  image_file: Mapped[str] = mapped_column(String(200),nullable=True, default=None)
  date_created: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(UTC)
  )
#   Part 1: The Core Type Hint
# Python
# posts: Mapped[list[Post]]
# What it means: This tells Python and your code editor that when you load a User object from the database, it will have a property called .posts, and that property will contain a standard Python list full of Post objects.

# In practice: You can write user.posts to instantly loop through everything that specific user has written without writing a single SELECT * FROM posts WHERE user_id = ... query.

# Part 2: The Linking Mechanism
# Python
# relationship(back_populates="author")
# What it means: This creates a two-way mirror between your two database tables.

# For this to work, your Post model must have a matching column pointing back to the user, like this: author: Mapped[User] = relationship(back_populates="posts").

# In practice: If you change a post's author in Python (post.author = user_objects), SQLAlchemy instantly updates the user's list (user_objects.posts) in memory, and vice-versa. It keeps your object-oriented data perfectly synced.

# Part 3: The Automated Cleanup (cascade="all, delete-orphan")
# This is the most powerful part of the line. It defines what happens to the child rows (posts) when something happens to the parent row (user).

# It breaks down into two distinct instructions:

# 1. The "all" Directive (Save & Delete Cascade)
# If you save a new User object to the database using db.add(user), SQLAlchemy will automatically look inside the user.posts list and save all of those new post objects at the exact same time. You don't have to call db.add() on every single post manually.

# If you delete a user (db.delete(user)), SQLAlchemy will automatically run a delete command on every single post belonging to that user.

# 2. The "delete-orphan" Directive (The Absolute Cleanup)
# An "orphan" post is a post that has been disconnected from its author. This happens if you remove a post from a user's list in Python code:

# Python
# # You remove the first post from the user's list
# my_user.posts.remove(some_post)
# db.commit()
# Without delete-orphan: MySQL would try to set that post's user_id column to NULL. If your database schema doesn't allow NULL values for user_id, your app crashes. If it does allow NULL, that post sits in your database forever, completely unlinked to anyone (a ghost record).

# With delete-orphan: The moment that post loses its connection to the user, SQLAlchemy realizes it is an "orphan" and permanently deletes it from the MySQL database automatically.
  posts:Mapped[list[Post]] = relationship(back_populates="author", cascade="all, delete-orphan")
# This is a "virtual" property. 
# It doesn't create a column in your SQL database. 
# Instead, it lets your React frontend easily grab a valid picture URL.
#  In your FastAPI route, you can call user.image_path, and it will automatically return their custom picture path, or fallback to a default avatar image.
  @property
  def image_path(self) -> str:
    if self.image_file:
      return f"/media/profile_pics/{self.image_file}"
    return "/static/profile_pics/default.jpg"
  
class Post(Base):
  __tablename__ = "posts"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  title: Mapped[str] = mapped_column(String(100), nullable=False)
  content: Mapped[str] = mapped_column(Text, nullable=False)
  user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id"),
    nullable=False,
    index=True
  )
  date_posted: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(UTC)
  )

  author: Mapped[User] = relationship(back_populates="posts")