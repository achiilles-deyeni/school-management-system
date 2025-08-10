# app.py or __init__.py
from flask import Flask, session

def create_app():
    app = Flask(__name__)
    app.secret_key = 'w7T@6zFv$2KmP9!xJ4eBhR^cQ1Lu&nDs'

    # Register blueprints, database init, etc.

    @app.context_processor
    def inject_current_user():
        return dict(current_user=session.get('user'))

    return app
