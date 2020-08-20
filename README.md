# Auxify 

Backend for a shared spotify play queue. Allow your friends and family to choose what plays next!

### Running the server

Recommended to run in a Python virtual environment.

- Install app requirements: `pip install -r requirements.txt`
- Install dev requirements: `pip install -r dev-requirements.txt`
- Create the database: `python schema/recreate_db.py`
- Run the server: `adev runserver main.py  --app-factory get_app -p 8080` OR `python main.py`
  - `adev` is recommended as it provides automatic reload of the server on code change
  - `.\runserver.ps1` if running in Powershell