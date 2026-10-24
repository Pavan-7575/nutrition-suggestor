from flask import Flask

from .config import Settings
from .routes import web


def create_app(test_config: dict | None = None) -> Flask:
    """Create the Nutrition Coach web application."""
    settings = Settings.from_environment()
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.update(settings.as_flask_config())
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(web)
    return app
