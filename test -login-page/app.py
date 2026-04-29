"""
Flask Application - Login Page Backend
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
from models import db, User
from jwt_utils import create_access_token, verify_token
from config import (
    SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS,
    SECRET_KEY,
    JWT_SECRET_KEY,
    DEBUG,
    HOST,
    PORT
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

# Initialize database and JWT
db.init_app(app)
jwt = JWTManager(app)
CORS(app)


@app.before_request
def init_db():
    """Initialize database on first request"""
    try:
        db.create_all()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")


@app.route("/")
def home():
    """Serve login page"""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Server is running"}), 200


@app.route("/api/register", methods=["POST"])
def register():
    """
    User Registration Endpoint
    Expected JSON: {"username": "...", "email": "...", "password": "..."}
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ("username", "email", "password")):
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        # Validation checks
        if not username or len(username) < 3:
            return jsonify({"success": False, "message": "Username must be at least 3 characters"}), 400
        
        if not email or "@" not in email:
            return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        if not password or len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({"success": False, "message": "Username already exists"}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "Email already registered"}), 409
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"New user registered: {username}")
        
        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "user": new_user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"success": False, "message": "Registration failed"}), 500


@app.route("/api/login", methods=["POST"])
def login():
    """
    User Login Endpoint
    Expected JSON: {"username": "...", "password": "..."}
    Returns: JWT token
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ("username", "password")):
            return jsonify({"success": False, "message": "Missing username or password"}), 400
        
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent user: {username}")
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        
        if not user.is_active:
            logger.warning(f"Login attempt with inactive user: {username}")
            return jsonify({"success": False, "message": "User account is disabled"}), 401
        
        # Verify password
        if not user.check_password(password):
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        
        # Create JWT token
        token = create_access_token(user.id, user.username, user.email)
        
        logger.info(f"User logged in: {username}")
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": user.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "message": "Login failed"}), 500


@app.route("/api/verify", methods=["POST"])
def verify():
    """
    Verify JWT Token Endpoint
    Expected JSON: {"token": "..."}
    """
    try:
        data = request.get_json()
        
        if not data or "token" not in data:
            return jsonify({"success": False, "message": "Token required"}), 400
        
        token = data.get("token")
        payload = verify_token(token)
        
        if not payload:
            return jsonify({"success": False, "message": "Invalid or expired token"}), 401
        
        return jsonify({
            "success": True,
            "message": "Token is valid",
            "payload": {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "token_type": payload.get("token_type"),
                "expires_at": payload.get("exp")
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({"success": False, "message": "Verification failed"}), 500


@app.route("/api/user/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """
    Get User Profile (requires valid JWT token in Authorization header)
    Expected header: Authorization: Bearer <token>
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "user": user.to_dict(),
            "token_claims": {
                "username": claims.get("username"),
                "email": claims.get("email")
            }}) 
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "user": user.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        return jsonify({"success": False, "message": "Failed to retrieve profile"}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"success": False, "message": "Internal server error"}), 500


@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid token errors"""
    return jsonify({"success": False, "message": "Invalid token"}), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token errors"""
    return jsonify({"success": False, "message": "Token has expired"}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    """Handle missing token errors"""
    return jsonify({"success": False, "message": "Authorization token is missing"}), 401


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    app.run(host=HOST, port=PORT, debug=DEBUG)
