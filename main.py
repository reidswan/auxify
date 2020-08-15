import logging
from aiohttp import web
import aiohttp_middlewares
import aiohttp.web_exceptions as exc

from auxify.config import Config
from auxify import routes

def main():
    Config.configure()
    Config.configure_logging()
    app = web.Application(middlewares=[
        aiohttp_middlewares.cors_middleware(allow_all=True),
        aiohttp_middlewares.error_middleware(ignore_exceptions=exc.HTTPRedirection)
    ])
    app.add_routes(routes.routes_tab)
    app.cleanup_ctx.append(Config.get_config().deferred_cleanup)
    web.run_app(app)


if __name__ == '__main__':
    main()
