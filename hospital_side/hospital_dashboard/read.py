import sqlite3

DB_PATH = r"C:\Users\Karan Kumar\PycharmProjects\Hospitle_emergency_system\Claude\hospital_side\hospital_dashboard\hospital.db"   # change if needed

def get_all_hospitals():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT 
            h.id,
            h.hospital_id,
            h.name,
            h.lat,
            h.lng,
            h.contact,
            h.address,
            bm.icu_available,
            bm.general_available,
            bm.oxygen_available
        FROM hospitals h
        LEFT JOIN bed_management bm
        ON h.hospital_id = bm.hospital_id
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    hospitals = []

    for row in rows:
        hospitals.append({
            "id": row["id"],                      # internal DB id
            "hospital_id": row["hospital_id"],    # public key
            "name": row["name"],
            "lat": row["lat"],
            "lng": row["lng"],
            "beds": {
                "icu": row["icu_available"] or 0,
                "general": row["general_available"] or 0,
                "oxygen": row["oxygen_available"] or 0
            },
            "contact": row["contact"],
            "address": row["address"]
        })
    return hospitals

print(get_all_hospitals())