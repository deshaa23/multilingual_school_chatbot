from datetime import date, timedelta
from backend.database import fetch_all


ATTENDANCE_REQUIREMENT = 75.0

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


# =========================================================
# EXTRACT MONTH
# =========================================================

def extract_month_from_question(question):

    if not question:
        return None

    text = str(question).strip().lower()

    for month, month_number in MONTH_MAP.items():

        if month in text:
            return month

    return None


# =========================================================
# WORKING DAYS
# =========================================================

def get_working_days(start_date, end_date):
    """
    Returns Monday-Friday working days.

    end_date is EXCLUSIVE.
    """

    working_days = []

    current = start_date

    while current < end_date:

        # Monday = 0
        # Sunday = 6

        if current.weekday() < 5:
            working_days.append(current)

        current += timedelta(days=1)

    return working_days


# =========================================================
# GET ATTENDANCE
# =========================================================

def get_attendance(
    student_id: int,
    metric=None,
    attendance_phrase=None,
    question=None
):

    today = date.today()

    start_date = None
    end_date = None

    selected_month = None
    selected_year = today.year

    # =====================================================
    # NORMALIZE
    # =====================================================

    if isinstance(metric, str):
        metric = metric.strip().lower()

    if isinstance(attendance_phrase, str):
        attendance_phrase = attendance_phrase.strip().lower()

    # =====================================================
    # RECOVER MONTH FROM QUESTION
    # =====================================================

    if not attendance_phrase and question:

        extracted_month = extract_month_from_question(
            question
        )

        if extracted_month:

            attendance_phrase = extracted_month

            print(
                f"Attendance month extracted from question: "
                f"{attendance_phrase}"
            )

    # =====================================================
    # SPECIFIC MONTH
    # =====================================================

    if attendance_phrase in MONTH_MAP:

        selected_month = MONTH_MAP[attendance_phrase]
        selected_year = today.year

        start_date = date(
            selected_year,
            selected_month,
            1
        )

        if selected_month == 12:

            end_date = date(
                selected_year + 1,
                1,
                1
            )

        else:

            end_date = date(
                selected_year,
                selected_month + 1,
                1
            )

        # Don't count future days
        if end_date > today + timedelta(days=1):

            end_date = today + timedelta(days=1)

    # =====================================================
    # CURRENT MONTH
    # =====================================================

    elif (
        metric == "monthly"
        or attendance_phrase == "this_month"
    ):

        selected_month = today.month
        selected_year = today.year

        start_date = date(
            today.year,
            today.month,
            1
        )

        end_date = today + timedelta(days=1)

    # =====================================================
    # LAST MONTH
    # =====================================================

    elif metric == "last_month":

        current_month_start = today.replace(day=1)

        end_date = current_month_start

        previous_month_last_day = (
            current_month_start - timedelta(days=1)
        )

        start_date = previous_month_last_day.replace(
            day=1
        )

        selected_month = start_date.month
        selected_year = start_date.year

    # =====================================================
    # DEBUG
    # =====================================================

    print()
    print("========== ATTENDANCE TOOL DEBUG ==========")
    print(f"Student ID       : {student_id}")
    print(f"Metric           : {metric}")
    print(f"Attendance Phrase: {attendance_phrase}")
    print(f"Question         : {question}")
    print(f"Today            : {today}")
    print(f"Selected Month   : {selected_month}")
    print(f"Selected Year    : {selected_year}")
    print(f"Start Date       : {start_date}")
    print(f"End Date         : {end_date}")
    print("============================================")

    # =====================================================
    # SQL
    # =====================================================

    if start_date is not None and end_date is not None:

        query = """
            SELECT
                attendance_date,
                status
            FROM attendance
            WHERE student_id = %s
              AND attendance_date >= %s
              AND attendance_date < %s
              AND attendance_date <= CURRENT_DATE
            ORDER BY attendance_date;
        """

        params = (
            student_id,
            start_date,
            end_date
        )

    else:

        query = """
            SELECT
                attendance_date,
                status
            FROM attendance
            WHERE student_id = %s
              AND attendance_date <= CURRENT_DATE
            ORDER BY attendance_date;
        """

        params = (
            student_id,
        )

    print()
    print("========== ATTENDANCE SQL ==========")
    print(query)
    print(f"PARAMS: {params}")
    print("====================================")
    print()

    # =====================================================
    # DATABASE
    # =====================================================

    results = fetch_all(
        query,
        params
    )

    # =====================================================
    # NORMALIZE RESULTS
    # =====================================================

    normalized_results = []

    for row in results:

        raw_status = row.get("status")

        status = (
            str(raw_status).strip().lower()
            if raw_status is not None
            else ""
        )

        normalized_results.append({
            "attendance_date": row["attendance_date"],
            "status": status
        })

    # =====================================================
    # COUNTS
    # =====================================================

    present = sum(
        1
        for row in normalized_results
        if row["status"] == "present"
    )

    absent = sum(
        1
        for row in normalized_results
        if row["status"] == "absent"
    )

    late = sum(
        1
        for row in normalized_results
        if row["status"] == "late"
    )

    unknown = sum(
        1
        for row in normalized_results
        if row["status"]
        not in {"present", "absent", "late"}
    )

    # =====================================================
    # DETERMINE WORKING DAYS
    # =====================================================

    if start_date is not None and end_date is not None:

        working_days = get_working_days(
            start_date,
            end_date
        )

        total_working_days = len(
            working_days
        )

    else:

        # Overall attendance:
        # use the date range covered by the records.

        if normalized_results:

            first_date = min(
                row["attendance_date"]
                for row in normalized_results
            )

            last_date = max(
                row["attendance_date"]
                for row in normalized_results
            )

            working_days = get_working_days(
                first_date,
                last_date + timedelta(days=1)
            )

            total_working_days = len(
                working_days
            )

        else:

            total_working_days = 0

    # =====================================================
    # MISSING DAYS
    # =====================================================

    recorded_dates = {
        row["attendance_date"]
        for row in normalized_results
    }

    missing_working_days = [
        day
        for day in working_days
        if day not in recorded_dates
    ]

    # =====================================================
    # IMPORTANT:
    #
    # Missing attendance rows are treated as ABSENT.
    #
    # This is what prevents:
    #
    # 22 present / 22 rows = 100%
    #
    # from incorrectly happening when there are
    # additional school days without attendance records.
    # =====================================================

    missing_count = len(
        missing_working_days
    )

    effective_absent = (
        absent + missing_count
    )

    total_days = (
        present
        + effective_absent
        + late
    )

    # =====================================================
    # PERCENTAGE
    # =====================================================

    if total_days > 0:

        percentage = (
            present / total_days
        ) * 100

    else:

        percentage = 0.0

    percentage = round(
        percentage,
        2
    )

    # =====================================================
    # DEBUG COUNTS
    # =====================================================

    print()
    print("========== ATTENDANCE CALCULATION ==========")
    print(f"Database rows       : {len(results)}")
    print(f"Present records     : {present}")
    print(f"Absent records      : {absent}")
    print(f"Late records        : {late}")
    print(f"Working days        : {total_working_days}")
    print(f"Missing working days: {missing_count}")
    print(f"Effective absent    : {effective_absent}")
    print(f"Total days counted  : {total_days}")
    print(f"Attendance %        : {percentage}")
    print("============================================")
    print()

    # =====================================================
    # ELIGIBILITY
    # =====================================================

    eligible = (
        percentage >= ATTENDANCE_REQUIREMENT
    )

    # =====================================================
    # PERIOD
    # =====================================================

    if attendance_phrase in MONTH_MAP:

        period = attendance_phrase.capitalize()

    elif (
        metric == "monthly"
        or attendance_phrase == "this_month"
    ):

        period = "Current Month"

    elif metric == "last_month":

        period = "Last Month"

    else:

        period = "Overall"

    # =====================================================
    # RETURN
    # =====================================================

    return {

        "type": "attendance",

        "success": True,

        "student_id": student_id,

        "metric": metric,

        "attendance_phrase": attendance_phrase,

        "question": question,

        "period": period,

        "month": selected_month,

        "year": (
            selected_year
            if selected_month
            else None
        ),

        "summary": {

            "total_days": total_days,

            "present": present,

            "absent": effective_absent,

            "late": late,

            "percentage": percentage
        },

        "eligibility": {

            "required_percentage":
                ATTENDANCE_REQUIREMENT,

            "current_percentage":
                percentage,

            "eligible":
                eligible
        },

        "records": normalized_results
    }