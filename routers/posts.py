from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from auth import CurrentUser
from databsase_async import Base, engine, get_db
from schemas import PostCreate, PostResponse, PostUpdate, UserCreate, UserPublic, UserUpdate

router = APIRouter()

@router.get('', response_model=list[PostResponse])
async def get_posts(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  if not current_user.id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to get the post details"
      )
  result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
  posts = result.scalars().all()
  return posts


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate,
current_user:CurrentUser,
 db: Annotated[AsyncSession, Depends(get_db)]):
  #  result = await db.execute(select(models.User).where(models.User.id == post.user_id))
  #  user = result.scalars().first()
  #  if not user:
  #    raise HTTPException(
  #      status_code=status.HTTP_404_NOT_FOUND,
  #      detail="USer not found"
  #    )

   new_post = models.Post(
     title = post.title,
     content = post.title,
     user_id = current_user.id
   )
   db.add(new_post)
   await db.commit()
   await db.refresh(new_post, attribute_names=["author"])
   return new_post


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.Post)
                            .options(selectinload(models.Post.author))
                            .where(models.Post.id == post_id))
  post = result.scalars().first()
  if not post:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
  return post

@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(post_id: int, post_data: PostCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.Post)
                            .options(selectinload(models.Post.author))
                            .where(models.Post.id == post_id))
  post = result.scalars().first()
  if not post:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
  # if post_data.user_id != post.user_id:
  #   result = await db.execute(select(models.User).where(models.User.id == post_data.user_id))
  #   user = result.scalars().first()
  #   if not user:
  #     raise HTTPException(
  #       status_code=status.HTTP_400_BAD_REQUEST,
  #       detail="USer not found"
  #     )
  if post.user_id != current_user.id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to update this post"
      )
  post.title = post_data.title
  post.content = post_data.content

  await db.commit()
  await db.refresh(post, attribute_names=["author"])
  return post
  
@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(post_id:int, post_data:PostUpdate,
                               current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.Post).where(models.Post.id == post_id))
  post = result.scalars().first()
  if not post:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Post not found"
    )
  if post.user_id != current_user.id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to update this post"
      )
  update_data = post_data.model_dump(exclude_unset=True) #exclude_unset
  for field, value in update_data.items():
    setattr(post, field, value)
  await db.commit()
  await db.refresh(post, attribute_names=["author"])
  return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deleted_post(post_id:int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(select(models.Post).where(models.Post.id == post_id))
  post = result.scalars().first()
  if not post:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Post not found"
    )
  if post.user_id != current_user.id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to update this post"
      )
  await db.delete(post)
  await db.commit()
