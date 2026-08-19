from fastapi import APIRouter, Depends, HTTPException
from backend.database import fetch_all, fetch_one, execute_query
from backend.routers.auth import require_role
from backend.schemas import teacherclass, teacherstudent

router = APIRouter(
    prefix="/teachers",
    tags=["teachers"]
)

@router.get(
    "/classes", response_model= list[teacherclass]
)
def get_my_classes(
    current_user = Depends(require_role("teacher"))
):
    query = """
    SELECT DISTINCT
    c.class_id,
    c.class_name,
    c.section,
    sub.subject_name
    FROM teachers t
    JOIN class_subjects cs
    ON t.teacher_id = cs.teacher_id
    JOIN classes c
    ON cs.class_id = c.class_id
    JOIN subjects sub
    ON cs.subject_id = sub.subject_id
    WHERE t.user_id = %s
    ORDER BY c.class_name, sub.subject_name;
    """

    return fetch_all(query, (current_user["user_id"],))

@router.get(
    "/students/{class_id}",
    response_model=list[teacherstudent]
)
def get_students_by_class(
    class_id: int,
    current_user=Depends(require_role("teacher"))
):
    check_query = """
    select 1
    from teachers t
    join class_subjects cs
    on t.teacher_id=cs.teacher_id
    where t.user_id =%s
    and cs.class_id =%s
    limit 1
    """
    allowed=fetch_one(
        check_query,
        (current_user["user_id"], class_id)
    )
    if not allowed:
        raise HTTPException(
            status_code= 403,
            detail= " You are not assigned to this class."
        )
    query = """
    select 
    student_id,
    first_name,
    last_name,
    roll_number,
    admission_number
    from students
    where class_id =%s
    order by roll_number;
    """
    return fetch_all(query,(class_id,))

