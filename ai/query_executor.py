from backend.database import fetch_all

def execute_sql(sql: str):
    """
    Execute a validated SELECT query and return the results.
    """

    # Escape % so psycopg doesn't interpret LIKE patterns
    sql = sql.replace("%", "%%")

    results = fetch_all(sql)

    return results