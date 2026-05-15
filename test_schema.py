from pydantic import BaseModel, ValidationError, Field, EmailStr, HttpUrl, SecretStr, field_validator, model_validator, computed_field, ConfigDict
from datetime import datetime, UTC
from functools import partial
from typing import Annotated, Literal
from uuid import uuid4, UUID
import json

# Why use Annotated?
# Cleanliness: It keeps your "Default Values" (like = 0) separate from your "Validation Rules" (like min_length=1).

# Reusability: You can create a "custom type" and reuse it everywhere. For example, if every username in your app must be 5+ characters, you can define it once:
# Why use this field validator instead of a simple type hint?
# While str tells Pydantic the data must be text, it doesn't stop someone from using weird symbols or mixed casing.

# As explained in the Python Pydantic Tutorial, field validators allow you to:

# Enforce Business Rules: (e.g., No special characters in names).

# Transform Data: (e.g., Converting email to lowercase or adding https:// to a URL automatically).

# Cross-Check Fields: You can even check if a "Password" field matches a "Confirm Password" field.
class User(BaseModel):
  model_config = ConfigDict(populate_by_name=True, strict=True,extra="allow", validate_assignment=
                            True,
                            frozen=True)
  # uid: Annotated[int, Field(gt=0)]
  # Field is a tool in Pydantic that lets you add "extra instructions" or "rules" to a specific piece of data in your model.
  uid:UUID = Field(alias="id", default_factory=uuid4)
  username: Annotated[str, Field(min_length=3, max_length=20)]
  # email:str
  email: EmailStr
  password: SecretStr
  website: HttpUrl | None = None
  age: Annotated[int, Field(ge=13, le=130)]
  verified_at: datetime | None = None
  bio:str = ""
  is_active: bool = True
  first_name: str = ''
  last_name: str = ''
  follower_count: int = 0

# @field_validator('username'): This is a Pydantic-specific decorator. It tells the model: "Whenever someone gives you a value for 'username', run it through this function first." It connects the function to the data field.
  @field_validator('username')
  @classmethod #@classmethod: This is a standard Python decorator. In Pydantic, validators must be class methods because they belong to the Model template itself, not to a specific instance of a user that already exists.
  def validate_username(cls, v: str) -> str: #Quick Tip: Notice the cls argument? Since this is a @classmethod, it refers to the class (the blueprint) rather than self (a specific object), which is why we don't use self here!
    if not v.replace('_','').isalnum():
      raise ValueError('Username must be aplphanumeric (underscore allowed)')
    return v.lower()
  
  @field_validator('website', mode="before")
  @classmethod
  def validate_email(cls, v: str | None) -> str | None:
    if isinstance(v, str) and not v.startswith(('https://','http://')):
      return f"https://{v}"
    return v
  
# In Pydantic, this combination of decorators allows you to create "virtual" fields that don't exist in your raw data but are calculated on the fly and included when you convert your model to a dictionary or JSON.

# Here is the breakdown of why both are used:

# 1. The @property Decorator
# This is standard Python. It turns a method into an "attribute."

# Without it: You would have to call user.is_influencer() like a function.

# With it: You can access it like a variable: user.is_influencer.

# In your code, it logicially checks the follower_count and returns True or False.

# 2. The @computed_field Decorator
# This is a Pydantic-specific feature. By default, Pydantic only "sees" the fields you defined at the top of the class (like username or age).

# The Problem: If you print post.model_dump(), a normal @property will be missing from the output.

# The Solution: @computed_field tells Pydantic: "Treat this property as a real piece of data. When I export this model to JSON or a dictionary, include is_influencer in the results."
  @computed_field
  @property
  def display_name(self) -> str:
    if self.first_name and self.last_name:
      return f"{self.first_name} {self.last_name}"
    return self.username

  @computed_field
  @property
  def is_influencer(self) -> bool:
    return self.follower_count >= 10000

try:
  user1 = User(username='123',email='Shikha@gmail.com',age=34, password='23324we', website='http://erwqrew.com', first_name="Shikha", last_name="Thakur")
except ValidationError as e:
  print(e,'error')
# user1.bio = 123
# print(user1.bio) # it is not validating on reassignment so it will not thorw error and give 123
# print(user1) #this will not give as dictionary
print(user1.model_dump_json(indent=2, by_alias=True, exclude={"password"},
                            include={'username','email'}), user1.password.get_secret_value()) #{'uid': 123, 'username': 'Shikha', 'email': 'abc@gmail.com', 'age': 34, 'verified_at': None, 'bio': '', 'is_active': True, 'full_name': None}
# print(user1.model_dump_json(indent=2)) #{"uid":123,"username":"Shikha","email":"abc@gmail.com","age":34,"verified_at":null,"bio":"","is_active":true,"full_name":null}
#with indent = 2
# {
#   "uid": 123,
#   "username": "Shikha",
#   "email": "abc@gmail.com",
#   "age": 34,
#   "verified_at": null,
#   "bio": "",
#   "is_active": true,
#   "full_name": null
# }

class Comment(BaseModel):
  content: str
  author_email: EmailStr
  likes:int = 0

# In the context of Pydantic and modern Python, Annotated is a way to attach extra metadata (information) to a type hint without changing the type itself.

# It is part of the standard typing library and is the preferred way to use Field in newer versions of Pydantic.

# How it works
# Think of Annotated as a container with two parts:

# The actual type: (e.g., str, int, list).

# The "Sticky Note": Extra rules or descriptions (like Field).
class BlogPost(BaseModel):
  title: Annotated[str, Field(min_length=3, max_length=20)]
  content: Annotated[str, Field(min_length=10, max_length=9999)]
  view_count: int = 0
  is_published: bool = False

  tags: list[str] = Field(default_factory=list)

  # create_at: datetime = Field(default_factory=lambda:datetime.now(tz=UTC))
#   What it is: A way to "pre-fill" some arguments of a function and save it for later.

# In your BlogPost example, you used it for the timestamp:
# default_factory=partial(datetime.now, UTC)

# The Problem: If you just wrote default=datetime.now(), the time would be frozen at the exact second you started your app. Every post created would have the exact same time.

# The Solution: partial creates a "package." Every time Pydantic creates a new blog post, it opens that package and runs datetime.now(UTC) at that specific moment. This ensures every post has its own unique, accurate timestamp.
  create_at: datetime = Field(default_factory=partial(datetime.now, tz=UTC))
                              
  author: User
# What it is: A way to say a variable can only be one of a few specific values.

# Instead of just saying a variable is a str (which could be anything from "apple" to "banana"), Literal forces it to be exactly what you list.

# Usage in your code: status: Literal['draft', 'published', 'archived']

# Why use it: It prevents typos. If a developer tries to set the status to "deleted", Pydantic will throw an error because it isn't in your "Literal" list.
  status: Literal['draft','published','archived'] = 'draft'
  slug: Annotated[str,Field(pattern=r"^[a-z0-9]+$")]
  comments: list[Comment] = Field(default_factory=list)

data = {
  "title": "Getting started",
  "content": "Here's how it begins",
  "slug": 'understandingpydantics',
  "author": {
    "username":"shikha",
    "email":'Shikha@gmail.com',
    "age":23,
    "password":"12345"
  },
  "comments":[
    {
      "content":"I think i usnderstand nested models",
      "author_email":"Shikha@gmail.com",
      "likes": 23
    },
    {
      "content":"LETS COVER FAST API NEXT",
      "author_email":"Shikha@1gmail.com",
      "likes": 232
    }
  ]
}
try:
  # post = BlogPost(**data)
  post = BlogPost.model_validate(data)
  print(post.model_dump_json(indent=2))
except ValidationError as e:
  print(e)


# User REgistration
class UserRegsitration(BaseModel):
  email:EmailStr
  password:str
  confirm_password: str

  @model_validator(mode="after")
  def passwords_match(self) -> "UserRegsitration":
    if self.password != self.confirm_password:
      raise ValueError("Passwords do not match")
    return self
  
try:
  registration = UserRegsitration(
    email="Shikha@gmail.com",
    password="123456",
    confirm_password="123456"
  )
except ValidationError as e:
  print(e)