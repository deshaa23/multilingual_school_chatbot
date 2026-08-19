from fastapi import APIRouter
from backend.database import fetch_all

router = APIRouter(
    prefix="/classes",
    tags=["Classes"]
)

@router.get("/")
def get_classes():

    classes = fetch_all(
        """
        SELECT
            class_id,
            class_name,
            section
        FROM classes
        ORDER BY class_name, section;
        """
    )

    return classes