from flask import Flask, jsonify, redirect
import os
from src.auth import auth
from src.bookmarks import bookmarks
from src.constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from src.database import Bookmark, db
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flasgger import Swagger, swag_from
from src.config.swagger import template, swagger_config

# baseDir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=str(os.getenv('SECRET_KEY')),
            SQLALCHEMY_DATABASE_URI=str(os.getenv('SQLALCHEMY_DB_URI')),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=str(os.getenv('JWT_SECRET_KEY')),

            SWAGGER={
                'title': 'Bookmarks API',
                'uiversion': 3
            }
        )
    else:
        app.config.from_mapping(test_config)

    db.app = app
    db.init_app(app)

    JWTManager(app)

    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)
    Swagger(app, config=swagger_config, template=template)

    # add value visits
    @app.get('/<short_url>')
    @swag_from('./docs/short_url.yml')
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()

        if bookmark:
            bookmark.visits = bookmark.visits+1
            db.session.commit()

            return redirect(bookmark.url)

    # error handling
    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify(
            {'error': 'Not Found'}
        )

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_500(e):
        return jsonify(
            {'error': 'Somethinh went wrong, we are working on it'}, HTTP_500_INTERNAL_SERVER_ERROR
        )

    return app


# app = create_app()
