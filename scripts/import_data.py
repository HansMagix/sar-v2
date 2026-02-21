import csv
import sqlite3
import os
import sys

# Ensure we can import config by adding project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def clean_float(value):
    if not value or value.strip() == '-' or value.strip() == '':
        return None
    try:
        return float(value)
    except ValueError:
        return None

def import_data():
    csv_path = os.path.join(os.getcwd(), 'degree_programmes_updt2025.csv')
    db_path = Config.PROGRAMMES_DB
    
    print(f"Reading from: {csv_path}")
    print(f"Writing to: {db_path}")

    # Connect to database (create if not exists)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('DROP TABLE IF EXISTS programmes')
    cursor.execute('''
        CREATE TABLE programmes (
            code TEXT PRIMARY KEY,
            institution TEXT,
            name TEXT,
            cutoff_2024 REAL,
            cutoff_2023 REAL,
            cutoff_2022 REAL,
            cutoff_2021 REAL,
            cutoff_2020 REAL,
            cutoff_2019 REAL,
            cutoff_2018 REAL,
            cluster TEXT,
            tags TEXT
        )
    ''')

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        count = 0
        for row in reader:
            # Map CSV columns to DB columns
            # CSV Header: prog_code,inst_name,prog_name,2018_cutoff,2019_cutoff,2020_cutoff,2021_cutoff,2022_cutoff,2023_cutoff,2024_cutoff,cluster
            
            code = row.get('prog_code')
            institution = row.get('inst_name')
            name = row.get('prog_name')
            
            # Handle dirty data for cutoffs
            c24 = clean_float(row.get('2024_cutoff'))
            c23 = clean_float(row.get('2023_cutoff'))
            c22 = clean_float(row.get('2022_cutoff'))
            c21 = clean_float(row.get('2021_cutoff'))
            c20 = clean_float(row.get('2020_cutoff'))
            c19 = clean_float(row.get('2019_cutoff'))
            c18 = clean_float(row.get('2018_cutoff'))
            
            cluster = row.get('cluster')
            
            # Simple tag derivation
            subjects = [] # New CSV doesn't seem to have subject_1 columns
            tags = ",".join(subjects) if subjects else ""

            if code:
                cursor.execute('''
                    INSERT OR IGNORE INTO programmes (code, institution, name, cutoff_2024, cutoff_2023, cutoff_2022, cutoff_2021, cutoff_2020, cutoff_2019, cutoff_2018, cluster, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (code, institution, name, c24, c23, c22, c21, c20, c19, c18, cluster, tags))
                count += 1

    conn.commit()
    conn.close()
    print(f"Successfully imported {count} programmes.")

if __name__ == '__main__':
    import_data()
