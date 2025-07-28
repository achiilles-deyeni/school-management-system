# app.py - Main application entry point
from flask import Flask
from config import Config
from database import init_db
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    init_db()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admins import admin_bp
    from routes.students import students_bp
    from routes.teachers import teachers_bp
    from routes.events import events_bp
    from routes.donations import donations_bp
    from routes.expenses import expenses_bp
    from routes.results import results_bp
    from routes.main import main_bp
    from routes.logs import logs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(teachers_bp, url_prefix='/teachers')
    app.register_blueprint(events_bp, url_prefix='/events')
    app.register_blueprint(donations_bp, url_prefix='/donations')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(results_bp, url_prefix='/results')
    app.register_blueprint(logs_bp, url_prefix='/logs')
    app.register_blueprint(main_bp)

    # Register error handlers
    from utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)