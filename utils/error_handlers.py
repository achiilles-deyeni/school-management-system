# utils/error_handlers.py - Error handling
from flask import render_template


def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', error=str(e)), 500