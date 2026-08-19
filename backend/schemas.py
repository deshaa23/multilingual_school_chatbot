from pydantic import BaseModel
from pydantic import EmailStr
from datetime import date, time
from decimal import Decimal

class student(BaseModel):
    student_id: int
    first_name:str
    last_name:str

class studentupdate(BaseModel):
    first_name: str
    last_name: str

class userregister(BaseModel):
    admission_number: str
    date_of_birth: date
    email:EmailStr
    password: str

class userlogin(BaseModel):
    email: EmailStr
    password: str

class studentprofile(BaseModel):
    student_id:int
    first_name: str
    last_name: str
    roll_number: int
    admission_number: str
    gender: str
    date_of_birth: date
    class_name: str
    section: str

class attendancerecord(BaseModel):
    attendance_date: date
    status: str
    
class resultrecord(BaseModel):
    subject_name:str
    exam_name: str
    marks_obtained: float
    maximum_marks: float

class assignmentrecord(BaseModel):
    title: str
    description: str
    assigned_date:date
    due_date: date
    subject_name:str

class teacherclass(BaseModel):
    class_id: int
    class_name: str
    section: str
    subject_name: str

class teacherstudent(BaseModel):
    student_id: int
    first_name: str
    last_name:str
    roll_number:int 
    admission_number:str

class studenttimetable(BaseModel):
    day_of_week: str
    start_time: time
    end_time: time
    room_number: str
    subject_name: str

class parentregister(BaseModel):
    first_name: str
    last_name: str
    admission_number: str
    date_of_birth: date

    email: EmailStr
    password: str

class parentprofile(BaseModel):
    parent_id: int
    first_name: str
    last_name:str
    email:str
    phone:str


class parentchild(BaseModel):
    student_id:int
    first_name: str
    last_name: str
    relationship: str
    class_name:str
    section: str

class parenttimetable(BaseModel):
    day_of_week: str
    period_number: int
    start_time: time
    end_time: time
    room_number:str
    subject_name: str

class parentassignment(BaseModel):
    assignment_id: int
    title:str
    description: str
    due_date:date
    subject_name: str

class parentresult(BaseModel):
    exam_name: str
    subject_name: str
    marks_obtained: float
    max_marks: float

