from datetime import datetime
from turtle import title
from typing import List, Literal
from unicodedata import category
from pydantic import BaseModel


class Post(BaseModel):
    title: str
    description: str
    mediaUrl: str | None = None
    authorId: str
    category: str
    date: datetime


class Comment(BaseModel):
    comment: str
    authorId: str
    date: datetime
    ratings: dict
    titleRating: Literal["True", "Partially True", "False"]
    descriptionRating: Literal["True", "Partially True", "False"]
    imageRating: Literal["True", "Partially True", "False"] | None = None


class User(BaseModel):
    name: str
    email: str
    profilePic: str
    postsCreated: List[str] | None = None
