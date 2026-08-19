from backend.database import fetch_all

def load_schema():
    columns_query="""
    select
        table_name,
        column_name,
        data_type
    from information_schema.columns
    where table_schema = 'public'
    order by table_name, ordinal_position;
    """
    columns_rows = fetch_all(columns_query)
    schema = {}
    for row in columns_rows:
        table = row["table_name"]

        if table not in schema:
            schema[table] = []

        schema[table].append(
            f"{row['column_name']} ({row['data_type']})"
        )

    fk_query = """
        SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public';
        """

    fk_rows=fetch_all(fk_query)

    schema_text = ""

    for table, columns in schema.items():
       schema_text += f"\nTable: {table}\n"
       schema_text += "\n".join(columns)
       schema_text += "\n"
       relations = [
           fk for fk in fk_rows if fk["table_name"]== table
       ]

       if relations:
           schema_text += "Relationships:\n"
           for fk in relations:
               schema_text+= (
                   f"{fk['column_name']} -> "
                   f"{fk['foreign_table_name']}."
                   f"{fk['foreign_column_name']}\n"
               )
           schema_text += "\n"
    return schema_text

    