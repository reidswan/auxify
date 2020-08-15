import sqlite3
from sys import argv, exit
import os

DEFAULT_DB_NAME = "auxify.db"
SCHEMA_LOCATION = "schema/schema.sql"

if not os.path.exists(SCHEMA_LOCATION):
    print("No schema file found at %s" % SCHEMA_LOCATION)
    print("Ensure you are running this from the project root (python schema/recreate_db.py)")
    exit(1)

if len(argv) >= 2:
    db_name = argv[1]
else:
    print("No DB name supplied; using default")
    db_name = DEFAULT_DB_NAME

if os.path.exists(db_name):
    print("Warning: %s already exists. Existing tables will not be modified or dropped." % db_name)
    print("To completely recreate the DB, delete that file first")

print("Running %s on DB '%s'" % (SCHEMA_LOCATION, db_name))

with open(SCHEMA_LOCATION) as sql_schema:
    contents = sql_schema.read()
    with sqlite3.connect(db_name) as db:
        db.executescript(contents)
        db.commit()
