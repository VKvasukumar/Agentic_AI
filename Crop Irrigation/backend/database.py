import sqlite3
import os
from backend.config import Config

def get_db():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database schema and seeds sample data if empty."""
    db_dir = os.path.dirname(Config.DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        
    db_file_exists = os.path.exists(Config.DATABASE_PATH) and os.path.getsize(Config.DATABASE_PATH) > 0
    
    if not db_file_exists:
        print("Database file does not exist or is empty. Initializing schema...")
        conn = get_db()
        
        # Read and execute schema
        schema_path = os.path.join(Config.BASE_DIR, 'database', 'crop_irrigation.sql')
        if os.path.exists(schema_path) and os.path.getsize(schema_path) > 0:
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
            conn.commit()
            print("Database schema created.")
            
            # Read and execute seed data
            seed_path = os.path.join(Config.BASE_DIR, 'database', 'sample_data.sql')
            if os.path.exists(seed_path) and os.path.getsize(seed_path) > 0:
                print("Seeding database with sample data...")
                with open(seed_path, 'r') as f:
                    conn.executescript(f.read())
                conn.commit()
                print("Database seeded.")
        else:
            print("Error: schema file not found or is empty!")
            
        conn.close()
    else:
        print("Database already initialized.")
