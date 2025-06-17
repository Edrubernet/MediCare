#!/usr/bin/env python3
"""
Простий скрипт для перевірки консультацій без Django shell
"""

# Це простий скрипт для перевірки того, що файли існують
import os

# Перевіряємо, чи файли існують
print("Перевірка файлів моделей:")
print(f"Consultation models: {os.path.exists('consultation/models.py')}")
print(f"Staff models: {os.path.exists('staff/models.py')}")
print(f"Patients models: {os.path.exists('patients/models.py')}")

# Перевіряємо базу даних SQLite
print(f"\nБаза даних:")
print(f"db.sqlite3 exists: {os.path.exists('db.sqlite3')}")

if os.path.exists('db.sqlite3'):
    import sqlite3
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Перевіряємо таблиці
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Таблиці в базі: {len(tables)}")
    
    # Перевіряємо консультації
    try:
        cursor.execute("SELECT COUNT(*) FROM consultation_consultation;")
        count = cursor.fetchone()[0]
        print(f"Консультацій у базі: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, start_time, status FROM consultation_consultation LIMIT 5;")
            consultations = cursor.fetchall()
            print("Перші 5 консультацій:")
            for cons in consultations:
                print(f"  - ID: {cons[0]}, Час: {cons[1]}, Статус: {cons[2]}")
    except sqlite3.OperationalError as e:
        print(f"Помилка при перевірці консультацій: {e}")
    
    conn.close()
else:
    print("База даних не знайдена")