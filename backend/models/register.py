from pydantic import BaseModel, EmailStr
from datetime import date


class StudentRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    class_id: int
    roll_number: int
    date_of_birth: date
    gender: str