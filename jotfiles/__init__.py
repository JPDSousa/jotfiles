from . import __meta__

__version__ = __meta__.version

from dataclasses import dataclass

from flask import Flask

from .trello.flask import blueprint as trello_bp


@dataclass
class Config:
    pass


def create_app(config: Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)
    app.register_blueprint(trello_bp)

    return app
