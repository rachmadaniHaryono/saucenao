"""Server module."""
from logging.handlers import TimedRotatingFileHandler
from urllib.parse import unquote_plus
import pprint
import logging
import os
import shutil
import tempfile

from flask import Flask, request, flash, send_from_directory, jsonify
from flask.cli import FlaskGroup
from flask.views import View
from flask_admin import Admin, BaseView, expose
from flask_admin._compat import text_type
from flask_admin.contrib.sqla import fields, ModelView
from sqlalchemy.orm.util import identity_key
import click

from . import models, views


def get_pk_from_identity(obj):
    """Monkey patck to fix flask-admin sqla error.

    https://github.com/flask-admin/flask-admin/issues/1588
    """
    res = identity_key(instance=obj)
    cls, key = res[0], res[1]  # NOQA
    return u':'.join(text_type(x) for x in key)


fields.get_pk_from_identity = get_pk_from_identity


def create_app(script_info=None):
    """create app."""
    app = Flask(__name__)
    default_log_file = 'saucenao.log'
    file_handler = TimedRotatingFileHandler(default_log_file, 'midnight')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('<%(asctime)s> <%(levelname)s> %(message)s'))
    app.logger.addHandler(file_handler)
    # reloader
    reloader = app.config['TEMPLATES_AUTO_RELOAD'] = bool(os.getenv('SAUCENAO_RELOADER')) or app.config['TEMPLATES_AUTO_RELOAD']  # NOQA
    if reloader:
        app.jinja_env.auto_reload = True
    # app config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SAUCENAO_SQLALCHEMY_DATABASE_URI') or 'sqlite:///saucenao_debug.db'  # NOQA
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SAUCENAO_SERVER_SECRET_KEY') or os.urandom(24)
    app.config['WTF_CSRF_ENABLED'] = False
    # debug
    debug = app.config['DEBUG'] = bool(os.getenv('SAUCENAO_DEBUG')) or app.config['DEBUG']
    if debug:
        app.config['DEBUG'] = True
        app.config['LOGGER_HANDLER_POLICY'] = 'debug'
        logging.basicConfig(level=logging.DEBUG)
        pprint.pprint(app.config)
        print('Log file: {}'.format(default_log_file))
    # app and db
    models.db.init_app(app)
    app.app_context().push()
    models.db.create_all()

    @app.shell_context_processor
    def shell_context():
        return {'app': app, 'db': models.db}

    # flask-admin
    app_admin = Admin(
        app, name='Saucenao', template_mode='bootstrap3',
        index_view=views.HomeView(name='Home', template='saucenow/index.html', url='/'))  # NOQA
    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """This is a management script for application."""
    pass


if __name__ == '__main__':
    cli()
