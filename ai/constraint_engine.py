import re


def insert_before_order_by(sql: str, clause: str) -> str:
    """
    Safely inserts a WHERE/AND clause before ORDER BY.
    """

    sql = sql.rstrip(";").strip()

    match = re.search(r"\bORDER\s+BY\b", sql, re.IGNORECASE)

    if match:
        index = match.start()

        before_order = sql[:index].rstrip()
        order_by = sql[index:]

        if re.search(r"\bWHERE\b", before_order, re.IGNORECASE):
            return before_order + "\n" + clause + "\n" + order_by
        else:
            return (
                before_order
                + "\nWHERE "
                + clause.removeprefix("AND ").strip()
                + "\n"
                + order_by
            )

    if re.search(r"\bWHERE\b", sql, re.IGNORECASE):
        return sql + "\n" + clause

    return (
        sql
        + "\nWHERE "
        + clause.removeprefix("AND ").strip()
    )


def apply_constraints(sql: str, plan: dict, user_context: dict) -> str:

    constraints = plan.get("constraints", {})
    context = plan.get("context", {})

    sql = sql.rstrip(";").strip()

    # =================================================
    # 1. FIX MARKS -> SUBJECTS RELATIONSHIP
    # =================================================

    if "FROM marks m" in sql and "m.subject_id" in sql:

        sql = sql.replace(
            "JOIN subjects s ON m.subject_id = s.subject_id",
            """
            JOIN class_subjects cs
                ON m.class_subject_id = cs.class_subject_id
            JOIN subjects s
                ON cs.subject_id = s.subject_id
            """
        )

    # =================================================
    # 2. REMOVE LLM-GENERATED PREVIOUS/LATEST EXAM LOGIC
    # =================================================

    sql = re.sub(
        r"\s*AND\s+e\.start_date\s*<\s*\(SELECT[\s\S]*?\)\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =================================================
    # 3. REMOVE INCORRECT EXAM NAME FILTERS
    # =================================================

    sql = re.sub(
        r"\s*AND\s+LOWER\(e\.exam_name\)\s+LIKE\s+'%[^']+%'\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =================================================
    # 4. REMOVE INCORRECT e.subject_name FILTER
    # =================================================

    sql = re.sub(
        r"\s*AND\s+e\.subject_name\s+LIKE\s+'%[^']+%'\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =================================================
    # 5. REMOVE INCORRECT sub.subject_name FILTER
    # =================================================

    sql = re.sub(
        r"\s*AND\s+LOWER\(sub\.subject_name\)\s+LIKE\s+'%[^']+%'\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =================================================
    # 6. REMOVE LLM-GENERATED LIMIT 1
    # =================================================

    sql = re.sub(
        r"\bLIMIT\s+1\s*$",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # =================================================
    # 7. ALWAYS ENFORCE LOGGED-IN STUDENT
    # =================================================

    student_id = user_context.get("student_id")

    if student_id:

        sql = re.sub(
            r"\bstudent_id\s*=\s*\d+",
            f"student_id = {student_id}",
            sql,
            flags=re.IGNORECASE
        )

    # =================================================
    # 8. SUBJECT FILTER
    # =================================================

    if context.get("subject"):

        subject = context["subject"]

        sql = insert_before_order_by(
            sql,
            f"AND LOWER(s.subject_name) = LOWER('{subject}')"
        )

    # =================================================
    # 9. ATTENDANCE CONSTRAINTS
    # =================================================

    if plan.get("intent") == "attendance":

        attendance_type = constraints.get("attendance")

        # ---------------------------------------------
        # ABSENT / MISSING DAYS
        # ---------------------------------------------

        if attendance_type in {"missing", "absent"}:

            sql = insert_before_order_by(
                sql,
                "AND LOWER(a.status) = 'absent'"
            )

        # ---------------------------------------------
        # PRESENT DAYS
        # ---------------------------------------------

        elif attendance_type == "present":

            sql = insert_before_order_by(
                sql,
                "AND LOWER(a.status) = 'present'"
            )

        # ---------------------------------------------
        # MONTH FILTER
        # ---------------------------------------------

        month = constraints.get("month")

        if month:

            sql = insert_before_order_by(
                sql,
                f"AND EXTRACT(MONTH FROM a.attendance_date) = {int(month)}"
            )

    # =================================================
    # 10. SPECIFIC EXAM
    # =================================================

    exam_constraint = constraints.get("exam")

    # Comparison questions need BOTH exams
    if (
        exam_constraint == "final"
        and plan.get("metric") != "exam_comparison"
    ):

        sql = insert_before_order_by(
            sql,
            "AND LOWER(e.exam_name) = LOWER('Final Examination')"
        )

    elif (
        exam_constraint == "midterm"
        and plan.get("metric") != "exam_comparison"
    ):

        sql = insert_before_order_by(
            sql,
            "AND LOWER(e.exam_name) = LOWER('Mid Term Examination')"
        )

    # =================================================
    # 11. LATEST EXAM
    # =================================================

    elif exam_constraint == "latest":

        sql = insert_before_order_by(
            sql,
            """
            AND m.exam_id = (
                SELECT exam_id
                FROM exams
                ORDER BY start_date DESC
                LIMIT 1
            )
            """
        )

    # =================================================
    # 12. PREVIOUS EXAM
    # =================================================

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

    # =================================================
    # 13. HISTORY
    # =================================================

    history = constraints.get("history")

    if history:

        sql = insert_before_order_by(
            sql,
            f"""
            AND m.exam_id IN (
                SELECT exam_id
                FROM exams
                ORDER BY start_date DESC
                LIMIT {int(history)}
            )
            """
        )

    # =================================================
    # DEBUG
    # =================================================

    print("\n===== FINAL SQL FROM CONSTRAINT ENGINE =====")
    print(sql)
    print("===========================================\n")

    return sql.strip() + ";"