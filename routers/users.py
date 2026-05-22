from typing import Annotated

from fastapi import FastAPI, APIRouter, Request, HTTPException, status, Path, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from databsase_async import Base, engine, get_db
from schemas import PostCreate, PostResponse, PostUpdate, UserCreate, UserResponse, UserUpdate

router = APIRouter()

@router.post("",
          response_model=UserResponse,
          status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
  username_lower = user.username.strip().lower()
  result = await db.execute(
    select(models.User).where(func.lower(models.User.username) == username_lower)
  )
  existing_user = result.scalars().first()
  if existing_user:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Username already exists"
    )
  email_lower = user.email.strip().lower()
  result = await db.execute(
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
  await db.commit()
  await db.refresh(new_user)
  return new_user

@router.get("", response_model=list[UserResponse])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.User))
  users = result.scalars().all()
  if not users:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail = "Users not found"
    )
  return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int,db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.User).where(models.User.id == user_id))
  user = result.scalars().first()
  if user:
    return user
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="USer not found")

# get user posts
@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.User).where(models.User.id == user_id))
  user = result.scalars().first()
  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="USer not found"
    )
  result = await db.execute(select(models.Post)
                            .options(selectinload(models.Post.author))
                            .where(models.Post.user_id == user_id))
  posts = result.scalars().all()
  return posts

@router.patch("/{user_id}", response_model=UserResponse)
async def user_update_fully(user_id:int, user_update: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.User).where(models.User.id == user_id))
  user = result.scalars().first()
  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail='User not found'
    )
  if user_update.username is not None and user_update.username != user.username:
    result = await db.execute(select(models.User).where(
      models.User.username == user_update.username
    ))
    existing_user = result.scalars().first()
    if existing_user:
      raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Username already exists'
      )
  if user_update.email is not None and user_update.email != user.email:
    result = await db.execute(select(models.User).where(
      models.User.email == user_update.email
    ))
    existing_email = result.scalars().first()
    if existing_email:
      raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Email already exists'
      )
  update_data = user_update.model_dump(exclude_unset=True)
  for field, value in update_data.items():
    setattr(user, field, value)
  await db.commit()
  await db.refresh(user)
  return user 

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db:Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.User).where(models.User.id == user_id))
  user = result.scalars().first()
  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="USer not found"
    )
  await db.delete(user)
  await db.commit()
