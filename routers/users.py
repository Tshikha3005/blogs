from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from databsase_async import get_db
from schemas import PostResponse, UserCreate, UserPublic, UserPrivate, UserUpdate, Token
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from auth import create_access_token, verify_access_token, hash_password, oauth2_scheme, verify_password, CurrentUser
from config import settings

router = APIRouter()

@router.post("",
          response_model=UserPrivate,
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
    email = user.email.strip().lower(),
    password_hash=hash_password(user.password)
  )
  db.add(new_user)
  await db.commit()
  await db.refresh(new_user)
  return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
  db: Annotated[AsyncSession, Depends(get_db)]
):
  # look up for user mail
  # Note: Oauth2passwordrequestform uses "username" field, but we treat as email
  result = await db.execute(select(models.User).where(func.lower(models.User.email) == form_data.username.lower()))
  user = result.scalars().first()
  # verify user exists and password is correct
  # Dontreveal which one failed (secuirty best practice)
  if not user or not verify_password(form_data.password, user.password_hash):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Incorrect email or password"
    )
  access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
  access_token = create_access_token(
    data={"sub": str(user.id)},
    expires_delta=access_token_expires
  )

  return Token(access_token=access_token, token_type="bearer")

# "/me"
@router.get("/me", response_model=UserPrivate)
async def get_current_user(
  # token: Annotated[str, Depends(oauth2_scheme)],
  # db: Annotated[AsyncSession, Depends(get_db)]
  current_user: CurrentUser
):
  # """Get the currently auhthneticated user"""
  return current_user
  # user_id = verify_access_token(token)
  # if user_id is None:
  #   raise HTTPException(
  #     status_code=status.HTTP_401_UNAUTHORIZED,
  #     detail="Invalid or expired token",
  #     headers={"WWW-Authenticate": "Bearer"}
  #   )
  # # validate user_id is a valid integer(defence against malfucntioned JWT)
  # try:
  #   user_id_int = int(user_id)
  # except(TypeError, ValueError):
  #   raise HTTPException(
  #     status_code=status.HTTP_401_UNAUTHORIZED,
  #     detail="Invalid or expired token",
  #     headers={"WWW-Authenticate": "Bearer"}
  #   )
  # result = await db.execute(
  #   select(models.User).where(models.User.id == user_id_int)
  # )
  # user = result.scalars().first()
  # if not user:
  #   raise HTTPException(
  #     status_code=status.HTTP_401_UNAUTHORIZED,
  #     detail="Not found",
  #     headers={"WWW-Authenticate": "Bearer"}
  #   )
  # return user

# Everything is working, but this route is doing 3 jobs:
# Handling HTTP request (@router.get)
# Querying database (select(models.User))
# Business logic (if not users)
@router.get("", response_model=list[UserPublic])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.User))
  users = result.scalars().all()
  if not users:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail = "Users not found"
    )
  return users

@router.get("/{user_id}", response_model=UserPublic)
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

@router.patch("/{user_id}", response_model=UserPrivate)
async def user_update_fully(user_id:int, user_update: UserUpdate,
                            current_user:CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  if user_id != current_user.id:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Not authorized to update the user"
    )
  result = await db.execute(select(models.User).where(models.User.id == user_id))
  user = result.scalars().first()
  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail='User not found'
    )
  if user_update.username is not None and user_update.username.lower() != user.username.lower():
    result = await db.execute(select(models.User).where(
      func.lower(models.User.username) == user_update.username.lower()
    ))
    existing_user = result.scalars().first()
    if existing_user:
      raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Username already exists'
      )
  if user_update.email is not None and user_update.email.lower() != user.email.lower():
    result = await db.execute(select(models.User).where(
      func.lower(models.User.email) == user_update.email.lower()
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
async def delete_user(user_id: int, current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
  if user_id != current_user.id:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="UNot authorized to delete the user"
    )
  result = await db.execute(select(models.User).where(models.User.id == user_id))
  user = result.scalars().first()
  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="USer not found"
    )
  await db.delete(user)
  await db.commit()
