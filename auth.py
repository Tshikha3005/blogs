from datetime import UTC, datetime, timedelta
import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from config import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status, HTTPException, Depends
import models
from databsase_async import get_db
from typing import Annotated

password_hash_context = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/users/token')

def hash_password(password: str) -> str:
  return password_hash_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
  return password_hash_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
  """ Create a JWT toekn """
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.now(UTC) + expires_delta
  else:
    expire = datetime.now(UTC) + timedelta(
      minutes=settings.access_token_expire_minutes
    )

  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(
    to_encode,
    settings.secret_key.get_secret_value(),
    algorithm=settings.algorithm
  )
  return encoded_jwt

# verify token
def verify_access_token(token:str) -> str | None:
  """Verify.a jwt token anf return the subject"""
  try:
    payload = jwt.decode(
      token,
      settings.secret_key.get_secret_value(),
      algorithms=[settings.algorithm],
      options={"require": ["exp","sub"]}
    )
  except jwt.InvalidTokenError:
    return None
  else:
    return payload.get("sub")
  
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> models.User:
  user_id = verify_access_token(token)
  if user_id is None:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid or expired token",
      headers={'WWW-Authenticated':'Bearer'}
    )
  try:
    user_id_int = int(user_id)
  except(TypeError, ValueError):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid or expired token",
      headers={'WWW-Authenticated':'Bearer'}
    )
  result = await db.execute(select(models.User).where(
    models.User.id == user_id_int
  ))
  user = result.scalars().first()
  if not user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="User not found",
      headers={"WWW-Authenticate":"Bearer"}
    )
  return user

CurrentUser = Annotated[models.User, Depends(get_current_user)]