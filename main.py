from datetime import timedelta
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import crud, models, schemas
from database import engine
from deps import get_db, ACCESS_TOKEN_EXPIRE_MINUTES
from token_helpers import verify_password, create_access_token, get_current_active_user

models.Base.metadata.create_all(bind=engine)
app = FastAPI()


@app.post("/users/register/", response_model=schemas.User, tags=["Account"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.post("/users/login/", response_model=schemas.Token, tags=["Account"])
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=schemas.User, tags=["Account"])
async def get_me(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)]
):
    return current_user


@app.post("/posts/", response_model=schemas.Post, tags=["Post"])
def create_post(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        post: schemas.PostCreate,
        db: Session = Depends(get_db),
):
    return crud.create_post(db=db, post=post, user_id=current_user.id)


@app.get("/posts/", response_model=list[schemas.Post], tags=["Post"])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = crud.get_posts(db, skip=skip, limit=limit)
    return posts


@app.get("/posts/{post_id}", response_model=schemas.Post, tags=["Post"])
def get_post(
        post_id: int,
        db: Session = Depends(get_db),
):
    db_post = crud.get_post_by_id(db, post_id=post_id)
    if not db_post:
        raise HTTPException(status_code=400, detail="Post not found")
    return db_post


@app.delete("/posts/{post_id}", response_model=schemas.Post, tags=["Post"])
def delete_post(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        post_id: int,
        db: Session = Depends(get_db),
):
    db_post = crud.get_post_by_id(db, post_id=post_id)
    if not db_post:
        raise HTTPException(status_code=400, detail="Post not found")
    if current_user.id != db_post.author_id:
        raise HTTPException(status_code=400, detail="You do not have permission to delete this post")

    post = crud.delete_post_by_id(db, post_id=post_id)
    return post


@app.patch("/posts/{post_id}", response_model=schemas.Post, tags=["Post"])
def patch_post(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        post_id: int,
        post: schemas.PostUpdate,
        db: Session = Depends(get_db),
):
    db_post = crud.get_post_by_id(db, post_id=post_id)
    if not db_post:
        raise HTTPException(status_code=400, detail="Post not found")
    if current_user.id != db_post.author_id:
        raise HTTPException(status_code=400, detail="You do not have permission to update this post")

    post = crud.update_post_by_id(db, post_id=post_id, post=post)
    return post


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
