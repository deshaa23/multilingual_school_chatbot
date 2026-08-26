from fastapi import FastAPI
#from backend.database import fetch_all, fetch_one, execute_query
#from backend.schemas import student
#from fastapi import HTTPException
#from backend.schemas import student, studentupdate
from backend.routers.students import router as student_router
from backend.routers.auth import router as auth_router
from backend.routers.teachers import router as teacher_router
from backend.routers.parents import router as parent_router
from backend.routers.chat import router as chat_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.class_routes import router as class_router


app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to the school chatbot API!"}

app.include_router(student_router)
app.include_router(auth_router)
app.include_router(teacher_router)
app.include_router(parent_router)
app.include_router(chat_router)
app.include_router(class_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://surf-arc-magnitude-westminster.trycloudflare.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
)

app.include_router(auth_router)
app.include_router(student_router)
app.include_router(chat_router)