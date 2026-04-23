import database
def count_rows():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    total = 0
    for table in tables:
        tname = table[0]
        if tname != "sqlite_sequence":
            cursor.execute(f"SELECT COUNT(*) FROM {tname}")
            c = cursor.fetchone()[0]
            print(f"{tname}: {c} rows")
            total += c
    print("TOTAL:", total)
    conn.close()
if __name__ == "__main__":
    count_rows()
