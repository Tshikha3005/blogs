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
  posts:Mapped[list[Post]] = relationship(back_populates="author")
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