
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from src.postulator.app import app

if __name__ == "__main__":
    app()
