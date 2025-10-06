import mysql.connector
from werkzeug.security import generate_password_hash
from db import get_db_connection

# Predefined users
users = [
    ("admin", "admin123", "admin"),
    ("staff", "staff123", "staff")
]

conn = get_db_connection()
cursor = conn.cursor()

for username, plain_pw, role in users:
    # ✅ Force PBKDF2-SHA256 instead of scrypt
    hashed_pw = generate_password_hash(
        plain_pw,
        method="pbkdf2:sha256",
        salt_length=16
    )

    cursor.execute("""
        INSERT INTO users (username, password, role) 
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            password = VALUES(password),
            role = VALUES(role)
    """, (username, hashed_pw, role))

conn.commit()
cursor.close()
conn.close()

print("✅ Users inserted/updated with PBKDF2-SHA256 hashes!")
