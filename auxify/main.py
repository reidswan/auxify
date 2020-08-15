import logging
from aiohttp import web
import aiohttp_middlewares

from auxify import config
from auxify import routes

def main():
    config.Config.configure()
    config.Config.configure_logging()
    app = web.Application(middlewares=[
        aiohttp_middlewares.cors_middleware(allow_all=True),
        aiohttp_middlewares.error_middleware()
    ])
    app.add_routes(routes.routes_tab)
    web.run_app(app)


if __name__ == '__main__':
    main()
