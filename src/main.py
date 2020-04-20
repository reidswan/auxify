import logging
from aiohttp import web
import config

import routes

def main():
    config.Config.configure()
    config.Config.configure_logging()
    app = web.Application()
    app.add_routes(routes.routes_tab)
    web.run_app(app)

main()
