import logging
from aiohttp import web
import config

import routes

def main():
    config.CONFIG = config.Config("Config.json")
    config.Config.configure_logging()
    app = web.Application()
    app.add_routes(routes.routes_tab)
    web.run_app(app)

main()
