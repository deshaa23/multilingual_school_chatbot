import re

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "MERGE", "CALL", "EXEC", "EXECUTE"
]

def validate_sql(sql: str) -> str:
    """
    Validates that the generated SQL is safe to execute.
    """

    # Remove markdown
    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")
    sql = sql.strip()

    # Extract SQL starting from SELECT
    match = re.search(r"(SELECT[\s\S]*)", sql, re.IGNORECASE)
    if match:
        sql = match.group(1).strip()

    # Remove trailing semicolon
    if sql.endswith(";"):
        sql = sql[:-1]

    # Only allow SELECT
    if not sql.upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed.")

    upper_sql = sql.upper()

    # Block dangerous SQL
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            raise ValueError(f"Unsafe SQL detected: {keyword}")

    # Prevent multiple statements
    if ";" in sql:
        raise ValueError("Multiple SQL statements are not allowed.")

    return sql