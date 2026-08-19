from fastapi import APIRouter, HTTPException
from fastapi import Depends
from backend.dependencies import require_role


from backend.database import(
    fetch_all,
    fetch_one,
    execute_query
)


from backend.schemas import(
    student,
    studentupdate,
    studentprofile,
    attendancerecord,
    resultrecord,
    assignmentrecord,
    studenttimetable
)

router = APIRouter(
    prefix="/students",
    tags=["students"]
)

@router.get("", response_model=list[student])
def get_students(current_user= Depends(require_role("admin"))):

    query = """
    SELECT
        student_id,
        first_name,
        last_name
    FROM students
    ORDER BY student_id;
    """

    students = fetch_all(query)

    return students

@router.get("/profile", response_model= studentprofile)
def get_my_profile(
    current_user= Depends(require_role("student"))
):
    query = """
    select 
    s.student_id,
    s.first_name,
    s.last_name,
    s.roll_number,
    s.admission_number,
    s.gender,
    s.date_of_birth,
    c.class_name,
    c.section
    from students s
    join classes c
        on s.class_id=c.class_id
    where s.user_id=%s;
    """
    profile = fetch_one(
        query,
        (current_user["user_id"],)
    )
    if profile is None:
        raise HTTPException(
            status_code= 404,
            detail= "Profile not found."
        )
    return profile

@router.get(
    "/attendance",
    response_model= list[attendancerecord]
)
def get_my_attendance(
    current_user= Depends(require_role("student"))
):
    query="""
    select
    a.attendance_date,
    a.status
    from attendance a
    join students s
    on a.student_id=s.student_id
    where s.user_id=%s
    order by a.attendance_date desc;
    """

    attendance = fetch_all(
        query,
        (current_user["user_id"],)
    )

    if not attendance:
        raise HTTPException(
            status_code=404,
            detail="No attendance records found."
        )
    return attendance

@router.get(
        "/results",
        response_model=list[resultrecord]
)
def get_my_results(
    current_user = Depends(require_role("student"))
):
    query= """
    select 
        sub.subject_name,
        e.exam_name,
        m.marks_obtained,
        m.maximum_marks
    from marks m
    join students s
        on m.student_id=s.student_id
    join class_subjects cs
        on m.class_subject_id = cs.class_subject_id
    join subjects sub
        on cs.subject_id = sub.subject_id
    join exams e
        on m.exam_id=e.exam_id
    where s.user_id = %s
    order by 
        e.exam_id,
        sub.subject_name;
    """
    
    results = fetch_all(
        query,
        (current_user["user_id"],)
    )

    if not results:
        raise HTTPException(
            status_code= 404,
            detail= "No results found."
        )
    return results

@router.get(
        "/assignments",
        response_model=list[assignmentrecord]
)
def get_my_assignments(
    current_user = Depends(require_role("student"))
): 
    query="""
    select
        a.title,
        a.description,
        a.assigned_date,
        a.due_date,
        sub.subject_name
    FROM assignments a
    JOIN class_subjects cs
        ON a.class_subject_id = cs.class_subject_id
    JOIN subjects sub
        ON cs.subject_id = sub.subject_id
    JOIN students s
        ON s.class_id = cs.class_id
    WHERE s.user_id = %s
    ORDER BY a.due_date;
    """

    assignments= fetch_all(
        query,
        (current_user["user_id"],)
    )

    if not assignments:
        raise HTTPException(
            status_code= 404,
            detail="No assignments found"
        )
    return assignments

@router.get(
    "/timetable",
    response_model= list[studenttimetable]
)
def get_timetable(
    current_user = Depends(require_role("student"))
):
    query="""
    SELECT
    tt.day_of_week,
    tt.period_number,
    tt.start_time,
    tt.end_time,
    tt.room_number,
    sub.subject_name
FROM timetable tt
JOIN class_subjects cs
ON tt.class_subject_id = cs.class_subject_id
JOIN subjects sub
ON cs.subject_id = sub.subject_id
JOIN students s
ON s.class_id = cs.class_id
WHERE s.user_id = %s
ORDER BY
CASE tt.day_of_week
    WHEN 'Monday' THEN 1
    WHEN 'Tuesday' THEN 2
    WHEN 'Wednesday' THEN 3
    WHEN 'Thursday' THEN 4
    WHEN 'Friday' THEN 5
    WHEN 'Saturday' THEN 6
END,
tt.period_number;
"""
    return fetch_all(
    query,
    (current_user["user_id"],)
    )

@router.get("/{student_id}",response_model=student)
def get_student(student_id: int, 
                current_user= Depends(require_role("admin"))):

    query="""
    select
    student_id,
    first_name,
    last_name
    from students
    where student_id = %s;
    """
    student_data = fetch_one(query,(student_id,))

    if student_data is None:
        raise HTTPException(
            status_code=404,
            detail="student not found"
        )
    return student_data

@router.put("/{student_id}")
def update_student(student_id: int, student: studentupdate, current_user= Depends(require_role("admin"))):

    query = """
    update students
    set
     first_name=%s,
     last_name=%s
    where student_id=%s;

"""
    rows_updated = execute_query(
    query,
    (
        student.first_name,
        student.last_name,
        student_id
    )
) 
    if rows_updated == 0:
        raise HTTPException(
            status_code=404,
            detail="student not found"
        )
    
    return {"message": "student updated successfully"}

@router.delete("/{student_id}")
def delete_student(student_id: int, current_user= Depends(require_role("admin"))):
    query="""
    delete from students
    where student_id = %s;
    """
    rows_deleted = execute_query(query, (student_id,))
    if rows_deleted==0:
        raise HTTPException(
            status_code= 404,
            detail="student not found"
        )
    return {"message": "student deleted successfully"}

