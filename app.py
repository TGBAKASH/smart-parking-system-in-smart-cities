"""
Smart City Parking System - Main Application
A peer-to-peer parking marketplace for smart cities
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from datetime import datetime
import os
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import configurations
from config import Config

# Import blueprints
from routes.auth import auth_bp
from routes.parking import parking_bp
from routes.booking import booking_bp
from routes.payment import payment_bp
from routes.chat import chat_bp
from routes.admin import admin_bp
from routes.user import user_bp
from routes.wallet import wallet_bp
from routes.review import review_bp
from routes.web import web_bp

# Import database models
from models.database import db

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS with proper configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": False
        }
    })
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Initialize MongoDB with safe timeout
    try:
        client = MongoClient(
            app.config['MONGO_URI'],
            serverSelectionTimeoutMS=4000,
            connectTimeoutMS=8000,
            socketTimeoutMS=8000
        )
        client.admin.command('ping')
        app.db = client.get_database()
        print("[OK] MongoDB connection successful!")
    except Exception as e:
        print(f"[WARN] MongoDB connection notice: {e}")
        app.db = None
    
    # Initialize database helper
    try:
        if hasattr(app, 'db') and app.db is not None:
            db.init_app(app)
            # Ensure density data baseline exists in DB in the background
            try:
                from seed_density_data import ensure_density_data_in_db
                threading.Thread(target=ensure_density_data_in_db, args=(app.db,), daemon=True).start()
            except Exception as seed_err:
                print(f"[WARN] Background seed notice: {seed_err}")
    except Exception as e:
        print(f"[WARN] Database initialization notice: {e}")
    
    # Register blueprints
    app.register_blueprint(web_bp)  # Web pages (no prefix)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(parking_bp, url_prefix='/api/parking')
    app.register_blueprint(booking_bp, url_prefix='/api/booking')
    app.register_blueprint(payment_bp, url_prefix='/api/payment')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
    app.register_blueprint(review_bp, url_prefix='/api/review')
    
    # Health check endpoint - always fast and non-blocking
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'Smart City Parking API'
        }), 200
    
    # Root API endpoint
    @app.route('/api')
    def api_index():
        return jsonify({
            'message': 'Smart City Parking API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'parking': '/api/parking',
                'booking': '/api/booking',
                'payment': '/api/payment',
                'chat': '/api/chat',
                'admin': '/api/admin',
                'user': '/api/user',
                'wallet': '/api/wallet'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
