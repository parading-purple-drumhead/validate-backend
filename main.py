'''
virt\scripts\activate.bat
uvicorn main:app --reload

'''


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import post, user

tags_metadata = [
    {
        "name": "Post",
        "description": "Endpoints related to operations on the **Posts** collection"
    },
    {
        "name": "User",
        "description": "Endpoints related to operations on the **Users** collection"
    }
]

app = FastAPI(
    title="Validate Backend",
    description="API endpoints for Validate website",
    version="1.0",
    openapi_tags=tags_metadata
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(
    post.router,
    prefix="/posts",
    tags=["Post"]
)

app.include_router(
    user.router,
    prefix="/users",
    tags=["User"]
)
