from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class PostBase(BaseModel):
    title: str
    text: str | None = None


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    pass


class PostAuthor(BaseModel):
    id: int
    email: str
    is_active: bool


class Post(PostBase):
    id: int
    author: PostAuthor

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    posts: list[Post] = []

    class Config:
        orm_mode = True
