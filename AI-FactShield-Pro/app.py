from flask import Flask, render_template
from config import Config
from database.db import init_db
from routes.home import home_bp
from routes.detect import detect_bp
from routes.dashboard import dashboard_bp
from routes.login import login_bp
from routes.register import register_bp
from routes.profile import profile_bp
from routes.history import history_bp
from routes.report import report_bp
from routes.feedback import feedback_bp
from routes.api import api_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db()

    app.register_blueprint(home_bp)
    app.register_blueprint(detect_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.context_processor
    def inject_globals():
        return {
            "app_name": "AI FactShield Pro",
            "app_tagline": "Detect • Analyze • Verify",
            "current_year": 2026,
        }

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
