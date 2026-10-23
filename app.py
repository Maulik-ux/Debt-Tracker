from flask import Flask
from config import Config
from database import init_db

# Import Controllers
from controllers.auth_controller import auth_bp
from controllers.dashboard_controller import dashboard_bp
from controllers.group_controller import group_bp
from controllers.expense_controller import expense_bp
from controllers.history_controller import history_bp
from controllers.optimizer_controller import optimizer_bp
from controllers.analytics_controller import analytics_bp
from controllers.settings_controller import settings_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLite database
init_db()

# Register All Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(group_bp)
app.register_blueprint(expense_bp)
app.register_blueprint(history_bp)
app.register_blueprint(optimizer_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(settings_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)