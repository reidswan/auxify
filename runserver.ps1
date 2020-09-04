$VENV_SCRIPT = ".\venv\Scripts\Activate.ps1" 

if (!($Env:VIRTUAL_ENV)) {
    echo "venv not active"
    if (!(Test-Path $VENV_SCRIPT)) {
        echo "No venv detected at $VENV_SCRIPT"
        exit
    } else {
        echo "Activating venv"
        Invoke-Expression $VENV_SCRIPT
    }
}

python -m aiohttp_devtools runserver main.py  --app-factory get_app -p 8080