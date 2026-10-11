from .account import account_bp
from .admin import admin_bp
from .auth import auth_bp
from .blocks import blocks_bp
from .menus import menus_bp
from .pages import pages_bp
from .settings import settings_bp


def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(blocks_bp)
    app.register_blueprint(menus_bp)
    app.register_blueprint(settings_bp)
