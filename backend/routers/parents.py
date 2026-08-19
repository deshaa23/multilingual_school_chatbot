from fastapi import APIRouter, Depends
from backend.dependencies import require_role
from backend.database import fetch_one, fetch_all
from fastapi import HTTPException
from backend.schemas import parentprofile, parentchild, parenttimetable, parentassignment, parentresult

router = APIRouter(
    prefix="/parents",
    tags=["parents"]
)

@router.get(
    "/profile",
    response_model=parentprofile
)
def get_parent_profile(
    current_user=Depends(require_role("parent"))
):
    query = """
    select
        parent_id,
        first_name,
        last_name,
        email,
        phone
    from parents
    where user_id=%s;
    """

    parent = fetch_one(query, (current_user["user_id"],))
    if parent is None:
        raise HTTPException(
        status_code=404,
        detail="Parent profile not found."
    )
    return parent


@router.get(
    "/children",
    response_model=list[parentchild]
)
def get_children(
    current_user=Depends(require_role("parent"))
):
    query = """
    select
        s.student_id,
        s.first_name,
        s.last_name,
        ps.relationship,
        c.class_name,
        c.section
    from parents p
    join parent_students ps
        on p.parent_id = ps.parent_id
    join students s
        on ps.student_id = s.student_id
    join classes c
        on s.class_id = c.class_id
    where p.user_id = %s
    order by s.student_id;
    """

    return fetch_all(query, (current_user["user_id"],))

@router.get(
    "/timetable",
    response_model=list[parenttimetable]
)
def get_parent_timetable(
    student_id: int | None = None,
    current_user=Depends(require_role("parent"))
):

    student_id = get_parent_student(
        current_user,
        student_id
    )

    query = """
    SELECT
        tt.day_of_week,
        tt.period_number,
        tt.start_time,
        tt.end_time,
        tt.room_number,
        sub.subject_name
    FROM students s
    JOIN class_subjects cs
        ON s.class_id = cs.class_id
    JOIN timetable tt
        ON cs.class_subject_id = tt.class_subject_id
    JOIN subjects sub
        ON cs.subject_id = sub.subject_id
    WHERE s.student_id=%s
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

    return fetch_all(query, (student_id,))

@router.get(
    "/assignments",
    response_model=list[parentassignment]
)
def get_parent_assignments(
    student_id: int | None = None,
    current_user=Depends(require_role("parent"))
):

    student_id = get_parent_student(
        current_user,
        student_id
    )

    query = """
    SELECT
        a.assignment_id,
        a.title,
        a.description,
        a.due_date,
        sub.subject_name
    FROM students s
    JOIN class_subjects cs
        ON s.class_id = cs.class_id
    JOIN assignments a
        ON cs.class_subject_id = a.class_subject_id
    JOIN subjects sub
        ON cs.subject_id = sub.subject_id
    WHERE s.student_id=%s
    ORDER BY a.due_date;
    """

    return fetch_all(query, (student_id,))

@router.get(
    "/results",
    response_model=list[parentresult]
)
def get_parent_results(
    student_id: int | None = None,
    current_user=Depends(require_role("parent"))
):

    student_id = get_parent_student(
        current_user,
        student_id
    )

    query = """
    SELECT
    e.exam_name,
    sub.subject_name,
    m.marks_obtained,
    m.maximum_marks AS max_marks
    FROM marks m
    JOIN exams e
    ON m.exam_id = e.exam_id
    JOIN class_subjects cs
    ON m.class_subject_id = cs.class_subject_id
    JOIN subjects sub
    ON cs.subject_id = sub.subject_id
    WHERE m.student_id = %s
    ORDER BY e.exam_name, sub.subject_name;
    """

    return fetch_all(query, (student_id,))

def get_parent_student(current_user, student_id=None):

    query = """
    SELECT
        s.student_id,
        s.first_name,
        s.last_name
    FROM parents p
    JOIN parent_students ps
        ON p.parent_id = ps.parent_id
    JOIN students s
        ON ps.student_id = s.student_id
    WHERE p.user_id = %s
    ORDER BY s.student_id;
    """

    students = fetch_all(
        query,
        (current_user["user_id"],)
    )

    if len(students) == 0:
        raise HTTPException(
            status_code=404,
            detail="No children found."
        )

   
    if len(students) == 1:
        return students[0]["student_id"]

    if student_id is None:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Multiple children found. Please provide student_id.",
                "children": students
            }
        )

    for student in students:
        if student["student_id"] == student_id:
            return student_id

    raise HTTPException(
        status_code=403,
        detail="You are not authorized to access this student's records."
    )