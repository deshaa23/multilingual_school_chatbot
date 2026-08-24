from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.chat1 import router as chat1_router


app = FastAPI(
    title="School Chatbot - New Pipeline"
)


@app.get("/")
def home():
    return {
        "message": "School Chatbot API - New Pipeline"
    }


app.include_router(chat1_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://jul-paul-musician-mil.trycloudflare.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)