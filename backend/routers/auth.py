from fastapi import APIRouter, HTTPException, Depends

from backend.schemas import userregister, parentregister
from backend.security import hash_password, verify_password
from psycopg.rows import dict_row
from backend.schemas import userlogin, userregister
from backend.auth_utils import create_access_token
from fastapi import Depends
from backend.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm

from backend.database import(
    fetch_one,
    execute_query,
    execute_returning,
    get_db
)

from backend.dependencies import(
    get_current_user,
    require_role
)

router = APIRouter(
    prefix= "/auth",
    tags=["authentication"]
)

@router.post("/register")
def register(user: userregister):

    query = """
    select
        student_id,
        user_id
    from students
    where admission_number = %s
    and date_of_birth = %s;
    """

    student = fetch_one(
        query,
        (
            user.admission_number,
            user.date_of_birth
        )
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid admission number or date of birth."
        )
    if student["user_id"] is not None:
        raise HTTPException(
            status_code=400,
            detail="Account already exists."
        )
    email_query="""
    select user_id
    from users
    where email=%s;
    """
    existing_user = fetch_one(
        email_query,
        (user.email,)
    )
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )
    
    hashed_password = hash_password(user.password)
    print("Generated hash:", hashed_password)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            insert_query = """
            insert into users(email,password_hash, role)
            values (%s, %s, %s)
            returning user_id;
            """

            cursor.execute(
                insert_query,
                (
                    user.email,
                    hashed_password,
                    "student"
                )
            )

            new_user = cursor.fetchone()

            update_query = """
            update students
            set user_id=%s
            where student_id=%s;
            """

            cursor.execute(
                update_query,
            (
                    new_user["user_id"],
                    student["student_id"]
            )
        )
    return {
        "message": "Registration successful."
        }

@router.post("/register/parent")
def register_parent(parent: parentregister):

    parent_query = """
    SELECT
        p.parent_id,
        p.user_id
    FROM parents p
    JOIN parent_students ps
        ON p.parent_id = ps.parent_id
    JOIN students s
        ON s.student_id = ps.student_id
    WHERE
        s.admission_number = %s
        AND s.date_of_birth = %s
        AND LOWER(p.first_name) = LOWER(%s)
        AND LOWER(p.last_name) = LOWER(%s);
    """

    parent_record = fetch_one(
        parent_query,
        (
            parent.admission_number,
            parent.date_of_birth,
            parent.first_name,
            parent.last_name
        )
    )

    if parent_record is None:
        raise HTTPException(
            status_code=404,
            detail="Parent details do not match school records."
        )

    if parent_record["user_id"] is not None:
        raise HTTPException(
            status_code=400,
            detail="Parent account already exists."
        )

    email_query = """
    SELECT user_id
    FROM users
    WHERE email = %s;
    """

    existing_user = fetch_one(
        email_query,
        (parent.email,)
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    hashed_password = hash_password(parent.password)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:

            insert_query = """
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, %s)
            RETURNING user_id;
            """

            cursor.execute(
                insert_query,
                (
                    parent.email,
                    hashed_password,
                    "parent"
                )
            )

            new_user = cursor.fetchone()

            update_query = """
            UPDATE parents
            SET
                user_id = %s,
                email = %s
            WHERE parent_id = %s;
            """

            cursor.execute(
                update_query,
                (
                    new_user["user_id"],
                    parent.email,
                    parent_record["parent_id"]
                )
            )

    return {
        "message": "Parent registration successful."
    }

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print("login endpoint called")
    print("username:", form_data)
    query="""
    select 
        user_id,
        email,
        password_hash,
        role
    from users
    where email=%s;
    """
    
    db_user = fetch_one(
        query,
        (form_data.username,)
    )
    
    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )
    if not verify_password(form_data.password, db_user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )
    
    token=create_access_token(
        {
            "sub": db_user["email"]
        }
    )
    return{
        "access_token": token,
        "token_type": "bearer"
    }
    
@router.get("/me")
def get_me(
    current_user= Depends(get_current_user)
):
    return current_user

@router.get("/student-only")
def student_only(
    current_user = Depends(require_role("student"))
):
    return {
        "message": "Welcome Student!",
        "user": current_user
    }

