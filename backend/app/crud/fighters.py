from backend.app.database import get_db

def get_all_fighters():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, nickname, height, weight, reach, stance, dob, record 
        FROM fighters
        ORDER BY name
    """)
    rows = cur.fetchall()

    conn.close()
    return [dict(row) for row in rows]