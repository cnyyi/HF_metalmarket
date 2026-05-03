import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from config import Config
from utils.database import DBConnection

app = Flask(__name__)
app.config.from_object(Config)

with app.app_context():
    with DBConnection() as conn:
        cursor = conn.cursor()

        sql = open('scripts/add_reversal_tables.sql', encoding='utf-8').read()
        for stmt in sql.split(';'):
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    err_msg = str(e).lower()
                    if 'already exists' in err_msg or 'already a column' in err_msg:
                        print(f'Skipped (already exists): {stmt[:60]}...')
                    else:
                        print(f'Error: {e}')
                        raise

        conn.commit()
        print('Migration OK')
