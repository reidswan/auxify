import logging
from aiohttp import web
import config

import routes

def main():
    config.Config.configure()
    config.Config.configure_logging()
    app = web.Application()
    app.add_routes(routes.routes_tab)
    app.cleanup_ctx.append(config.Config.get_config().deferred_cleanup)
    web.run_app(app)


if __name__ == '__main__':
    main()
