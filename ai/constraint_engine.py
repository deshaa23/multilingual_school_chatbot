import re


# =========================================================
# INSERT CLAUSE BEFORE ORDER BY
# =========================================================

def insert_before_order_by(sql: str, clause: str) -> str:
    """
    Safely inserts a WHERE/AND clause before ORDER BY.
    """

    sql = sql.rstrip(";").strip()

    match = re.search(
        r"\bORDER\s+BY\b",
        sql,
        re.IGNORECASE
    )

    if match:

        index = match.start()

        before_order = sql[:index].rstrip()
        order_by = sql[index:]

        if re.search(
            r"\bWHERE\b",
            before_order,
            re.IGNORECASE
        ):

            return (
                before_order
                + "\n"
                + clause
                + "\n"
                + order_by
            )

        else:

            return (
                before_order
                + "\nWHERE "
                + clause.removeprefix("AND ").strip()
                + "\n"
                + order_by
            )

    # No ORDER BY

    if re.search(
        r"\bWHERE\b",
        sql,
        re.IGNORECASE
    ):

        return (
            sql
            + "\n"
            + clause
        )

    return (
        sql
        + "\nWHERE "
        + clause.removeprefix("AND ").strip()
    )


# =========================================================
# CHECK WHETHER SUBJECT FILTER ALREADY EXISTS
# =========================================================

def has_subject_filter(sql: str) -> bool:
    """
    Detect whether SQL already contains a subject_name filter.

    Supports both:
        sub.subject_name
        s.subject_name

    This prevents duplicate subject conditions.
    """

    patterns = [

        r"\bsub\.subject_name\b",

        r"\bs\.subject_name\b",

    ]

    for pattern in patterns:

        if re.search(
            pattern,
            sql,
            re.IGNORECASE
        ):

            return True

    return False


# =========================================================
# GET SUBJECT ALIAS
# =========================================================

def get_subject_alias(sql: str) -> str | None:
    """
    Detect the alias used for the subjects table.

    Examples:

        JOIN subjects sub
        JOIN subjects s
        FROM subjects sub

    Returns:
        'sub'
        's'
        None
    """

    patterns = [

        r"\bJOIN\s+subjects\s+([a-zA-Z_][a-zA-Z0-9_]*)",

        r"\bFROM\s+subjects\s+([a-zA-Z_][a-zA-Z0-9_]*)",

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            sql,
            re.IGNORECASE
        )

        if match:

            return match.group(1)

    return None


# =========================================================
# APPLY CONSTRAINTS
# =========================================================

def apply_constraints(
    sql: str,
    plan: dict,
    user_context: dict
) -> str:

    constraints = plan.get(
        "constraints",
        {}
    ) or {}

    context = plan.get(
        "context",
        {}
    ) or {}

    sql = sql.rstrip(";").strip()

    # =====================================================
    # DEBUG
    # =====================================================

    print("\n===== CONSTRAINT ENGINE =====")
    print("Constraints:", constraints)
    print("Context:", context)
    print("=============================\n")

    # =====================================================
    # 1. FIX MARKS -> SUBJECTS RELATIONSHIP
    # =====================================================

    if (
        "FROM marks m" in sql.lower()
        and "m.subject_id" in sql.lower()
    ):

        sql = re.sub(
            r"JOIN\s+subjects\s+s\s+ON\s+m\.subject_id\s*=\s*s\.subject_id",
            """
            JOIN class_subjects cs
                ON m.class_subject_id = cs.class_subject_id
            JOIN subjects s
                ON cs.subject_id = s.subject_id
            """,
            sql,
            flags=re.IGNORECASE
        )

    # =====================================================
    # 2. REMOVE LLM-GENERATED PREVIOUS/LATEST EXAM LOGIC
    # =====================================================

    sql = re.sub(
        r"\s*AND\s+e\.start_date\s*<\s*\(SELECT[\s\S]*?\)\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =====================================================
    # 3. REMOVE INCORRECT EXAM NAME FILTERS
    # =====================================================

    sql = re.sub(
        r"\s*AND\s+LOWER\(e\.exam_name\)\s+LIKE\s+'%[^']+%'\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =====================================================
    # 4. REMOVE INCORRECT e.subject_name FILTER
    # =====================================================

    sql = re.sub(
        r"\s*AND\s+e\.subject_name\s+LIKE\s+'%[^']+%'\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =====================================================
    # 5. REMOVE INCORRECT sub.subject_name LIKE FILTER
    # =====================================================

    sql = re.sub(
        r"\s*AND\s+LOWER\(sub\.subject_name\)\s+LIKE\s+'%[^']+%'\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =====================================================
    # 6. REMOVE LLM-GENERATED LIMIT 1
    # =====================================================

    sql = re.sub(
        r"\bLIMIT\s+1\s*$",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =====================================================
    # 7. ALWAYS ENFORCE LOGGED-IN STUDENT
    # =====================================================

    student_id = user_context.get(
        "student_id"
    )

    if student_id:

        # -------------------------------------------------
        # Replace an existing student_id condition
        # -------------------------------------------------

        sql = re.sub(
            r"\bstudent_id\s*=\s*\d+",
            f"student_id = {int(student_id)}",
            sql,
            flags=re.IGNORECASE
        )

        # -------------------------------------------------
        # If there is no student_id filter, add one
        # -------------------------------------------------

        if not re.search(
            r"\bstudent_id\s*=\s*\d+",
            sql,
            re.IGNORECASE
        ):

            sql = insert_before_order_by(
                sql,
                f"AND st.student_id = {int(student_id)}"
            )

    # =====================================================
    # 8. SUBJECT FILTER
    # =====================================================

    # Subject may be stored in either:
    #
    # plan["context"]["subject"]
    #
    # or
    #
    # plan["constraints"]["subject"]
    #
    # Support both.

    subject = (
        context.get("subject")
        or constraints.get("subject")
    )

    if subject:

        subject = str(
            subject
        ).strip()

        if subject:

            # -------------------------------------------------
            # IMPORTANT:
            #
            # If the SQL already contains a subject_name
            # condition, DO NOT ADD ANOTHER ONE.
            #
            # This fixes the Chemistry problem.
            # -------------------------------------------------

            if not has_subject_filter(sql):

                subject_alias = get_subject_alias(
                    sql
                )

                if subject_alias:

                    safe_subject = (
                        subject
                        .replace("'", "''")
                    )

                    sql = insert_before_order_by(
                        sql,
                        (
                            "AND LOWER(TRIM("
                            f"{subject_alias}.subject_name"
                            ")) = LOWER("
                            f"'{safe_subject}'"
                            ")"
                        )
                    )

    # =====================================================
    # 9. ATTENDANCE CONSTRAINTS
    # =====================================================

    if plan.get("intent") == "attendance":

        attendance_type = constraints.get(
            "attendance"
        )

        # -------------------------------------------------
        # ABSENT
        # -------------------------------------------------

        if attendance_type in {
            "missing",
            "absent"
        }:

            sql = insert_before_order_by(
                sql,
                "AND LOWER(a.status) = 'absent'"
            )

        # -------------------------------------------------
        # PRESENT
        # -------------------------------------------------

        elif attendance_type == "present":

            sql = insert_before_order_by(
                sql,
                "AND LOWER(a.status) = 'present'"
            )

        # -------------------------------------------------
        # LATE
        # -------------------------------------------------

        elif attendance_type == "late":

            sql = insert_before_order_by(
                sql,
                "AND LOWER(a.status) = 'late'"
            )

        # -------------------------------------------------
        # MONTH
        # -------------------------------------------------

        month = constraints.get(
            "month"
        )

        if month:

            try:

                month_number = int(
                    month
                )

                if 1 <= month_number <= 12:

                    sql = insert_before_order_by(
                        sql,
                        (
                            "AND EXTRACT("
                            "MONTH FROM a.attendance_date"
                            f") = {month_number}"
                        )
                    )

            except (
                TypeError,
                ValueError
            ):

                pass

        # -------------------------------------------------
        # YEAR
        # -------------------------------------------------

        year = constraints.get(
            "year"
        )

        if year:

            try:

                year_number = int(
                    year
                )

                sql = insert_before_order_by(
                    sql,
                    (
                        "AND EXTRACT("
                        "YEAR FROM a.attendance_date"
                        f") = {year_number}"
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                pass

    # =====================================================
    # 10. SPECIFIC EXAM
    # =====================================================

    exam_constraint = constraints.get(
        "exam"
    )

    # Comparison questions need BOTH exams.
    #
    # Therefore do NOT force a single exam for
    # exam_comparison.

    if (
        exam_constraint == "final"
        and plan.get("metric") != "exam_comparison"
    ):

        sql = insert_before_order_by(
            sql,
            (
                "AND LOWER(e.exam_name) = "
                "LOWER('Final Examination')"
            )
        )

    elif (
        exam_constraint == "midterm"
        and plan.get("metric") != "exam_comparison"
    ):

        sql = insert_before_order_by(
            sql,
            (
                "AND LOWER(e.exam_name) = "
                "LOWER('Mid Term Examination')"
            )
        )

    # =====================================================
    # 11. LATEST EXAM
    # =====================================================

    elif exam_constraint == "latest":

        sql = insert_before_order_by(
            sql,
            """
            AND e.exam_id = (
                SELECT exam_id
                FROM exams
                ORDER BY start_date DESC
                LIMIT 1
            )
            """
        )

    # =====================================================
    # 12. PREVIOUS EXAM
    # =====================================================

    elif exam_constraint == "previous":

        sql = insert_before_order_by(
            sql,
            """
            AND m.exam_id = (
                SELECT exam_id
                FROM exams
                ORDER BY start_date DESC
                OFFSET 1
                LIMIT 1
            )
            """
        )

    # =====================================================
    # 13. HISTORY
    # =====================================================

    history = constraints.get(
        "history"
    )

    if history:

        try:

            history_number = int(
                history
            )

            if history_number > 0:

                sql = insert_before_order_by(
                    sql,
                    f"""
                    AND m.exam_id IN (
                        SELECT exam_id
                        FROM exams
                        ORDER BY start_date DESC
                        LIMIT {history_number}
                    )
                    """
                )

        except (
            TypeError,
            ValueError
        ):

            pass

    # =====================================================
    # 14. REMOVE DUPLICATE SUBJECT CONDITIONS
    # =====================================================

    # This is intentionally conservative.
    #
    # We do NOT blindly remove all subject conditions,
    # because the original SQL may legitimately contain
    # a subject filter.
    #
    # The main protection is that we don't add a second
    # filter if one already exists.

    # =====================================================
    # DEBUG
    # =====================================================

    print("\n===== FINAL SQL FROM CONSTRAINT ENGINE =====")
    print(sql)
    print("===========================================\n")

    return sql.strip() + ";"