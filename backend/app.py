# app.py — Clean, optimized, production-ready with Celery tasks for mail & CSV export
import os
from functools import wraps
from datetime import datetime, timedelta, time
import pytz
import csv
from dotenv import load_dotenv

# Load environment variables once
load_dotenv()

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache
from flask_mail import Mail, Message
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import or_, func

# -----------------------
# Basic configuration
# -----------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IST = pytz.timezone("Asia/Kolkata")

app = Flask(__name__)
CORS(app, supports_credentials=True, expose_headers=["Content-Disposition"])

# Flask config (from env)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change_me_secret_key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_SEC', 7200))

# DB
DB_FILENAME = os.getenv('DB_FILENAME', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, DB_FILENAME))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Redis / Celery
app.config['broker_url'] = os.getenv('broker_url', 'redis://localhost:6379/0')
app.config['result_backend'] = os.getenv('result_backend', app.config['broker_url'])

# Mail config (Flask-Mail)
app.config.update(
    MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=int(os.getenv('MAIL_PORT', 587)),
    MAIL_USE_TLS=os.getenv('MAIL_USE_TLS', 'True') == 'True',
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER')
)

MAIL_RECIVER = app.config['MAIL_DEFAULT_SENDER']

# Caching (optional Redis)
cache = Cache(config={
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/0')
})
cache.init_app(app)

db = SQLAlchemy(app)
mail = Mail(app)
jwt = JWTManager(app)

# -----------------------
# Celery factory + beat schedule
# -----------------------
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config["broker_url"],
        broker=app.config["result_backend"]
    )

    celery.conf.update(app.config)

    # Set global timezone for all scheduled tasks
    celery.conf.timezone = "Asia/Kolkata"
    celery.conf.enable_utc = False

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    celery.conf.beat_schedule = {
        "daily_reminders": {
            "task": "tasks.send_daily_reminder",
            "schedule": crontab(hour=18, minute=00),  # 6 PM IST
        },
        "monthly_report": {
            "task": "tasks.send_monthly_report",
            "schedule": crontab(day_of_month=1, hour=6, minute=0),  # 6 AM IST
        },
    }

    return celery

celery = make_celery(app)

# -----------------------
# Models
# -----------------------
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)  # email/login
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    pin_code = db.Column(db.String(10))
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    address = db.Column(db.String(200))
    pin_code = db.Column(db.String(10))
    number_of_spots = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Boolean, default=False)
    spots = db.relationship('ParkingSpot', backref='lot', cascade='all, delete-orphan', lazy=True)

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='A')  # 'A' available, 'R' reserved

class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)  # 'Reserved' / 'Released' / 'Occupied'
    total_cost = db.Column(db.Float)
    vehicle_number = db.Column(db.String(30), nullable=True)

    user = db.relationship('User', backref='reservations')
    lot = db.relationship('ParkingLot', backref='reservations')
    spot = db.relationship('ParkingSpot', backref='reservations')

# -----------------------
# Helper utilities
# -----------------------
def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        @jwt_required(optional=True)
        def wrapper(*args, **kwargs):
            # Allow OPTIONS preflight without requiring JWT
            if request.method == "OPTIONS":
                return jsonify({"message": "CORS preflight OK"}), 200

            claims = get_jwt()
            token_role = claims.get('role')

            if token_role != required_role:
                return jsonify({'message': f'Access denied: {required_role} only'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def safe_filename(s: str) -> str:
    """Create a filesystem-safe filename part."""
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s)

# -----------------------
# Initialization: create DB and admin from env (no hard-coded password)
# -----------------------
@app.before_request
def create_db_and_admin():
    db.create_all()
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')

    if not admin_username or not admin_password:
        app.logger.warning("ADMIN_USERNAME or ADMIN_PASSWORD is missing in .env — admin not created.")
        return

    if not User.query.filter_by(username=admin_username).first():
        admin = User(
            username=admin_username,
            name='Admin',
            address='HQ',
            pin_code='000000',
            role='admin'
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Admin user created from .env")

# -----------------------
# Sync util
# -----------------------
def update_spot_status_from_reservation(reservation: Reservation):
    spot = db.session.get(ParkingSpot, reservation.spot_id)
    if not spot:
        return
    if reservation.status == "Reserved":
        spot.status = "R"
    elif reservation.status in ["Released", "Cancelled"]:
        spot.status = "A"
    db.session.commit()

# -----------------------
# Auth routes (SQLAlchemy + flask_jwt_extended)
# -----------------------

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    required_fields = ['username', 'password']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'{field} is required'}), 400
            
    username = data['username']
    password = data['password']
    name = data.get('name')
    address = data.get('address')
    pin_code = data.get('pin_code')
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'Username already exists'}), 400

    password_hash = generate_password_hash(password)

    new_user = User(
        username=username,
        password_hash=password_hash,
        name=name,
        address=address,
        pin_code=pin_code,
        role='user'
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'username and password required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    additional_claims = {'role': user.role}
    access_token = create_access_token(identity=user.username, additional_claims=additional_claims)
    return jsonify({
        'success': True,
        'username': user.username,
        'role': user.role,
        'token': access_token
    }), 200

# -----------------------
# Admin routes (parking lots CRUD)
# -----------------------

@app.route('/api/admin/parking-lots', methods=['GET'])
@role_required('admin')
def admin_get_parking_lots():
    lots = ParkingLot.query.all()   # admin sees both active + disabled
    result = []

    for lot in lots:
        available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()

        result.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'price': lot.price,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'number_of_spots': lot.number_of_spots,
            'available_spots': available_spots,
            'is_deleted': bool(lot.is_deleted),       # ⭐ show active/disabled
            'spots': [
            {
                'id': s.id,
                'status': "DISABLED" if s.status == "INACTIVE" else s.status,
                'reserved_by': (
                    Reservation.query.join(User)
                    .with_entities(User.name)
                    .filter(
                        Reservation.spot_id == s.id,
                        Reservation.status.in_(["Reserved", "Occupied"])
                    )
                    .order_by(Reservation.id.desc())
                    .first()
                )[0] if s.status in ["R", "Reserved", "Occupied"] else None
            }
            for s in lot.spots
            ]
        })

    return jsonify(result), 200

@app.route('/api/admin/parking-lots', methods=['POST'])
@role_required('admin')
def admin_create_parking_lot():
    data = request.get_json() or {}
    required_fields = ['prime_location_name', 'price', 'address', 'pin_code', 'number_of_spots']

    for f in required_fields:
        if f not in data:
            return jsonify({"message": f"Missing field: {f}"}), 400

    try:
        lot = ParkingLot(
            prime_location_name=data['prime_location_name'],
            price=float(data['price']),
            address=data['address'],
            pin_code=data['pin_code'],
            number_of_spots=int(data['number_of_spots']),
            is_deleted=False
        )
        db.session.add(lot)
        db.session.commit()

        # create spots
        for _ in range(lot.number_of_spots):
            db.session.add(ParkingSpot(lot_id=lot.id, status='A'))
        db.session.commit()

        cache.delete('parking_lots_all')
        return jsonify({"message": "Parking lot created successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error creating parking lot: {str(e)}"}), 500

@app.route('/api/admin/parking-lots/<int:lot_id>', methods=['PUT'])
@role_required('admin')
def admin_update_parking_lot(lot_id):
    try:
        lot = db.session.get(ParkingLot, lot_id)
        if not lot:
            return jsonify({'message': 'Parking lot not found'}), 404

        data = request.get_json() or {}

        if 'prime_location_name' in data:
            lot.prime_location_name = data['prime_location_name']
        if 'price' in data:
            lot.price = float(data['price'])
        if 'address' in data:
            lot.address = data['address']
        if 'pin_code' in data:
            lot.pin_code = data['pin_code']

        old_spots = lot.number_of_spots
        new_spots = int(data.get('number_of_spots', old_spots))

        if new_spots != old_spots:
            if new_spots > old_spots:
                # ADD NEW SPOTS
                for _ in range(new_spots - old_spots):
                    db.session.add(ParkingSpot(lot_id=lot.id, status='A'))
            else:
                # REMOVE ONLY AVAILABLE SPOTS
                to_delete = old_spots - new_spots
                available_spots = ParkingSpot.query.filter_by(
                    lot_id=lot.id, status='A'
                ).order_by(ParkingSpot.id.desc()).limit(to_delete).all()

                if len(available_spots) < to_delete:
                    return jsonify({"message": "Cannot reduce spots — not enough free spots"}), 400

                for sp in available_spots:
                    db.session.delete(sp)

            lot.number_of_spots = new_spots

        db.session.commit()
        cache.delete('parking_lots_all')

        return jsonify({'message': 'Parking lot updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating parking lot: {str(e)}'}), 500

@app.route('/api/admin/parking-lots/<int:lot_id>', methods=['DELETE'])
@role_required('admin')
def admin_delete_parking_lot(lot_id):
    try:
        lot = db.session.get(ParkingLot, lot_id)
        if not lot:
            return jsonify({'message': 'Parking lot not found'}), 404

        # Block delete if any spot is Reserved/Occupied
        occupied_count = ParkingSpot.query.filter(
            ParkingSpot.lot_id == lot.id,
            ParkingSpot.status != 'A'
        ).count()

        if occupied_count > 0:
            return jsonify({
                'message': 'Cannot delete: Some spots are occupied or reserved.',
                'occupied_spots': occupied_count
            }), 400

        # ⭐ SOFT DELETE — keep data for future use
        lot.is_deleted = True

        # Disable all spots
        ParkingSpot.query.filter_by(lot_id=lot.id).update({"status": "INACTIVE"})

        db.session.commit()
        return jsonify({'message': 'Parking lot disabled successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting parking lot: {str(e)}'}), 500

@app.route('/api/admin/parking-lots/<int:lot_id>/restore', methods=['POST'])
@role_required('admin')
def admin_restore_parking_lot(lot_id):
    try:
        lot = db.session.get(ParkingLot, lot_id)
        if not lot:
            return jsonify({'message': 'Parking lot not found'}), 404

        if not lot.is_deleted:
            return jsonify({'message': 'Parking lot is already active'}), 400

        # Reactivate the lot
        lot.is_deleted = False

        # Reactivate spots that were marked INACTIVE
        updated = ParkingSpot.query.filter_by(lot_id=lot.id, status='INACTIVE').update({"status": "A"})
        # If there are no spot rows at all (unlikely), ensure spots exist matching number_of_spots
        existing_spot_count = ParkingSpot.query.filter_by(lot_id=lot.id).count()
        if existing_spot_count < (lot.number_of_spots or 0):
            to_create = (lot.number_of_spots or 0) - existing_spot_count
            for _ in range(to_create):
                db.session.add(ParkingSpot(lot_id=lot.id, status='A'))

        db.session.commit()
        cache.delete('parking_lots_all')

        return jsonify({
            'message': 'Parking lot restored successfully',
            'lot_id': lot.id,
            'reactivated_spots': int(updated or 0),
            'total_spots': ParkingSpot.query.filter_by(lot_id=lot.id).count()
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.exception("Error restoring parking lot %s: %s", lot_id, e)
        return jsonify({'message': f'Error restoring parking lot: {str(e)}'}), 500

# -----------------------
# Admin search & users
# -----------------------

@app.route('/api/admin/search', methods=['GET'])
@role_required('admin')
def admin_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Search query required"}), 400
    
    # Convert to lower-case for flexible matching
    search = f"%{query}%"

    # -------------------------
    # 1) USER SEARCH
    # -------------------------
    users = User.query.filter(
        or_(
            User.name.ilike(search),
            User.username.ilike(search),
            User.address.ilike(search),
            User.pin_code.ilike(search),
            User.role.ilike(search)          # NEW: search by role
        )
    ).all()

    # -------------------------
    # 2) PARKING LOT SEARCH
    # -------------------------

    status_query = query.lower()
    status_filter = None

    # Status keyword mapping
    if status_query in ["active", "enabled", "not deleted"]:
        status_filter = ParkingLot.is_deleted.is_(False)
    elif status_query in ["disabled", "inactive", "deleted", "off"]:
        status_filter = ParkingLot.is_deleted.is_(True)

    # IMPORTANT FIX
    if status_filter is not None:
        lots = ParkingLot.query.filter(status_filter).all()
    else:
        search = f"%{query}%"
        lots = ParkingLot.query.filter(
            or_(
                ParkingLot.prime_location_name.ilike(search),
                ParkingLot.address.ilike(search),
                ParkingLot.pin_code.ilike(search),
                func.cast(ParkingLot.price, db.String).ilike(search),
                func.cast(ParkingLot.id, db.String).ilike(search)
            )
        ).all()


    # -------------------------
    # 3) RESERVATION SEARCH
    # -------------------------
    reservation_filter = [
        Reservation.status.ilike(search),
        Reservation.vehicle_number.ilike(search),
        func.cast(Reservation.id, db.String).ilike(search),        # NEW: search res ID
        func.cast(Reservation.spot_id, db.String).ilike(search),   # NEW: search spot ID
        func.cast(Reservation.lot_id, db.String).ilike(search),    # NEW: search lot ID
        User.name.ilike(search),
        User.username.ilike(search),
        ParkingLot.prime_location_name.ilike(search)
    ]

    reservations = (
        Reservation.query
        .outerjoin(User)              # OUTER JOIN avoids NULL join break
        .outerjoin(ParkingLot)
        .filter(or_(*reservation_filter))
        .all()
    )

    # -------------------------
    # FORMAT RESPONSE
    # -------------------------
    return jsonify({
        "users": [{
            "username": u.username,
            "name": u.name,
            "address": u.address,
            "pin_code": u.pin_code,
            "role": u.role
        } for u in users],

        "lots": [{
            "id": l.id,
            "location": l.prime_location_name,
            "address": l.address,
            "pin_code": l.pin_code,
            "price": l.price,
            "is_deleted": bool(l.is_deleted)
        } for l in lots],

        "reservations": [{
            "id": r.id,
            "user": {
                "id": r.user.id if r.user else None,
                "name": r.user.name if r.user else None,
                "username": r.user.username if r.user else None,
            },
            "lot": {
                "id": r.lot.id if r.lot else None,
                "name": r.lot.prime_location_name if r.lot else None,
                "is_deleted": r.lot.is_deleted if r.lot else None
            },
            "spot": {
                "id": r.spot_id
            },
            "status": r.status,
            "vehicle_number": r.vehicle_number,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "total_cost": r.total_cost
        } for r in reservations]
    })

@app.route('/api/admin/users', methods=['GET'])
@role_required('admin')
def admin_get_users():
    users = User.query.filter_by(role='user').all()
    return jsonify([{'id': u.id, 'name': u.name, 'username': u.username, 'address': u.address, 'pin_code': u.pin_code, 'role': u.role} for u in users]), 200

# -----------------------
# Admin summary (single endpoint returning all needed pieces)
# -----------------------
@app.route('/api/admin/summary', methods=['GET'])
def admin_summary():
    # Occupancy
    active_lot_ids = [l.id for l in ParkingLot.query.filter_by(is_deleted=False).all()]
    total_spots = ParkingSpot.query.filter(ParkingSpot.lot_id.in_(active_lot_ids)).count()
    reserved = ParkingSpot.query.filter(ParkingSpot.lot_id.in_(active_lot_ids), ParkingSpot.status == 'R').count()
    available = ParkingSpot.query.filter(ParkingSpot.lot_id.in_(active_lot_ids), ParkingSpot.status == 'A').count()
    occupancy = {"reserved": reserved, "available": available, "total": total_spots}

    # Revenue per lot
    revenue_results = db.session.query(ParkingLot.prime_location_name, func.sum(Reservation.total_cost)).join(
        Reservation, Reservation.lot_id == ParkingLot.id).group_by(ParkingLot.prime_location_name).all()
    lots = [row[0] for row in revenue_results]
    revenue = [float(row[1] or 0) for row in revenue_results]
    revenue_per_lot = {"lots": lots, "revenue": revenue}

    # Daily revenue for last N days (default 7 or 10)
    days = int(os.getenv('ADMIN_DAILY_RANGE_DAYS', 7))
    today_ist = datetime.now(IST).date()
    lastN = [today_ist - timedelta(days=i) for i in range(days-1, -1, -1)]
    dates, values = [], []
    for single_date in lastN:
        day_start = datetime.combine(single_date, time.min)
        day_end = datetime.combine(single_date + timedelta(days=1), time.min)
        if day_start.tzinfo is None:
            day_start = IST.localize(day_start)
        if day_end.tzinfo is None:
            day_end = IST.localize(day_end)
        day_sum = db.session.query(func.sum(Reservation.total_cost)).filter(Reservation.end_time >= day_start, Reservation.end_time < day_end).scalar()
        dates.append(single_date.strftime("%Y-%m-%d"))
        values.append(float(day_sum or 0))
    daily_revenue = {"dates": dates, "values": values}

    # Duration distribution
    reservations = Reservation.query.all()
    buckets = {"0-1 Hour": 0, "1-3 Hours": 0, "3-6 Hours": 0, "6-9 Hours": 0, "9+ Hours": 0}
    for r in reservations:
        if r.start_time and r.end_time:
            diff = (r.end_time - r.start_time).total_seconds() / 3600
            if diff <= 1:
                buckets["0-1 Hour"] += 1
            elif diff <= 3:
                buckets["1-3 Hours"] += 1
            elif diff <= 6:
                buckets["3-6 Hours"] += 1
            elif diff <= 9:
                buckets["6-9 Hours"] += 1
            else:
                buckets["9+ Hours"] += 1
    duration_summary = {"buckets": list(buckets.keys()), "counts": list(buckets.values())}

    return jsonify({"success": True, "occupancy": occupancy, "revenue_per_lot": revenue_per_lot, "daily_revenue": daily_revenue, "duration_distribution": duration_summary}), 200

# -----------------------
# User routes (allocate, reservations, terminate, parking-lots, details, summary)
# -----------------------
@app.route('/api/user/allocate', methods=['POST'])
def allocate_spot():
    try:
        data = request.get_json() or {}
        username = data.get('user')
        lot_id = data.get('lot_id')
        vehicle_no = data.get('vehicle_no')
        if not username or not lot_id or not vehicle_no:
            return jsonify({'message': 'Missing username, lot_id or vehicle_no'}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        lot = db.session.get(ParkingLot, int(lot_id))
        if not lot or lot.is_deleted:
            return jsonify({'message': 'Parking lot not found'}), 404

        spot = ParkingSpot.query.filter_by(lot_id=lot.id, status="A").first()
        if not spot:
            return jsonify({'message': 'No available spots'}), 400

        spot.status = "R"
        reservation = Reservation(
            user_id=user.id,
            lot_id=lot.id,
            spot_id=spot.id,
            vehicle_number=vehicle_no,
            start_time=datetime.now(IST),
            status="Reserved"
        )
        db.session.add(reservation)
        db.session.commit()

        # Sync status (committed)
        update_spot_status_from_reservation(reservation)

        return jsonify({"message": "Spot reserved successfully!", "reservation_id": reservation.id, "spot_id": spot.id, "vehicle_no": vehicle_no}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/user/reservations/<string:username>', methods=['GET'])
def get_user_reservations(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    reservations = Reservation.query.filter(Reservation.user_id == user.id, Reservation.status.in_(["Reserved", "Occupied"])).all()
    result = []
    for r in reservations:
        result.append({
            "reservation_id": r.id,
            "lot_name": r.lot.prime_location_name + (" (disabled)" if r.lot and r.lot.is_deleted else "") if r.lot else None,
            "spot_id": r.spot_id,
            "price": r.lot.price if r.lot else None,
            "Vehicle_no": r.vehicle_number,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "status": r.status
        })
    return jsonify(result)

@app.route('/api/user/reservations/terminate/<int:reservation_id>', methods=['POST'])
def terminate_reservation(reservation_id):
    try:
        reservation = db.session.get(Reservation, reservation_id)
        if not reservation:
            return jsonify({'message': 'Reservation not found'}), 404
        if reservation.status == "Released":
            return jsonify({'message': 'Reservation already released'}), 400

        end_time = datetime.now(IST)
        reservation.end_time = end_time
        reservation.status = "Released"

        spot = db.session.get(ParkingSpot, reservation.spot_id)
        if spot:
            spot.status = "A"

        # compute total_cost
        if reservation.start_time:
            start_time = reservation.start_time
            if start_time.tzinfo is None:
                start_time = IST.localize(start_time)
            duration_hours = (end_time - start_time).total_seconds() / 3600
            if duration_hours > 24:
                days = int(duration_hours // 24)
                remaining = duration_hours % 24
                daily_rate = 18 * float(reservation.lot.price)
                total_cost = round(days * daily_rate + remaining * float(reservation.lot.price))
            else:
                duration_hours = max(duration_hours, 0.25)
                total_cost = round(duration_hours * float(reservation.lot.price))
            reservation.total_cost = total_cost

        db.session.commit()
        update_spot_status_from_reservation(reservation)
        return jsonify({'message': 'Spot released successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error terminating reservation: {str(e)}'}), 500

@app.route('/api/user/parking-lots', methods=['GET'])
def user_get_parking_lots():
    try:
        lots = ParkingLot.query.filter_by(is_deleted=False).all()
        result = []
        for lot in lots:
            available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
            result.append({
                'id': lot.id,
                'prime_location_name': lot.prime_location_name,
                'price': lot.price,
                'address': lot.address,
                'pin_code': lot.pin_code,
                'number_of_spots': lot.number_of_spots,
                'available_spots': available_spots
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching parking lots: {str(e)}'}), 500

@app.route('/api/user/details/<string:username>', methods=['GET'])
def get_user_details(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"username": user.username, "name": user.name, "address": user.address, "pin_code": user.pin_code}), 200

# -----------------------
# User summary
# -----------------------
@app.route('/api/user/summary', methods=['GET'])
@jwt_required()
def user_summary():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    user_id = user.id
    reservations = Reservation.query.filter_by(user_id=user_id).all()
    total_reservations = len(reservations)
    total_cost = sum(r.total_cost or 0 for r in reservations)
    total_hours = sum(((r.end_time - r.start_time).total_seconds() / 3600) for r in reservations if r.end_time and r.start_time)

    hist = []
    for r in reservations:
        hist.append({
            "lot_name": r.lot.prime_location_name + (" (disabled)" if r.lot and r.lot.is_deleted else "") if r.lot else None,
            "spot_id": r.spot_id,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "status": r.status,
            "vehicle_no": r.vehicle_number,
            "total_cost": r.total_cost or 0
        })

    reserved_count = Reservation.query.filter_by(user_id=user_id, status="Reserved").count()
    released_count = Reservation.query.filter_by(user_id=user_id, status="Released").count()
    used_spots = ParkingSpot.query.filter(ParkingSpot.status == "R").count()
    free_spots = ParkingSpot.query.filter(ParkingSpot.status == "A").count()

    # weekly cost (last 5 weeks, oldest->newest)
    weekly_cost = []
    weeks = []
    today = datetime.now(IST)
    current_monday = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(5):
        week_start = current_monday - timedelta(weeks=(4 - i))  # oldest first
        week_end = week_start + timedelta(days=7)
        week_label = f"Week {5 - (4 - i)} ({week_start.strftime('%d %b')})"
        week_data = Reservation.query.filter(Reservation.user_id == user_id, Reservation.start_time >= week_start, Reservation.start_time < week_end).all()
        weekly_cost.append(sum(r.total_cost or 0 for r in week_data))
        weeks.append(week_label)

    return jsonify({
        "success": True,
        "summary": {"total_reservations": total_reservations, "total_cost": total_cost, "total_hours": round(total_hours, 2)},
        "history": hist,
        "graphs": {"reserved": reserved_count, "released": released_count, "used_spots": used_spots, "free_spots": free_spots, "weeks": weeks, "weekly_cost": weekly_cost}
    }), 200

# -----------------------
# Code supports synchronous download via /api/export-csv and async email via POST /api/user/export/<username>
# -----------------------
@app.route('/api/export-csv', methods=['GET'])
@jwt_required()
def export_csv():
    username = request.args.get("username")
    date_param = request.args.get("date")  # YYYY-MM-DD optional

    if not username:
        return jsonify({"message": "username is required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    safe_name = safe_filename(user.name or "user")
    download_date = date_param or datetime.now(IST).strftime("%Y-%m-%d")
    now = datetime.now(IST)
    hh_mm = now.strftime("%H-%M")
    filename = f"{safe_name}-{download_date}-{hh_mm}.csv"

    export_dir = os.path.join(BASE_DIR, "exports")
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, filename)

    # Get only Released reservations
    rows = Reservation.query.filter_by(
        user_id=user.id, status="Released"
    ).order_by(Reservation.start_time.asc()).all()

    # write CSV
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Reservation ID", "Lot Name", "Spot ID", "Vehicle Number", "Start Time", "End Time", "Status", "Total Cost"])
        for r in rows:
            writer.writerow([
                r.id,
                r.lot.prime_location_name if r.lot else "",
                r.spot_id,
                r.vehicle_number or "",
                r.start_time.isoformat() if r.start_time else "",
                r.end_time.isoformat() if r.end_time else "",
                r.status,
                r.total_cost or 0
            ])

    return send_file(filepath, as_attachment=True, download_name=filename)

# Async CSV export: Celery task that creates CSV and emails to user
@celery.task(name='tasks.generate_csv_and_email')
def task_generate_csv_and_email(user_id):
    with app.app_context():
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "user not found"}

        safe_name = safe_filename(user.name or "user")
        now = datetime.now(IST)
        filename = f"{safe_name}-{now.strftime('%Y-%m-%d')}-{now.strftime('%H-%M')}.csv"

        export_dir = os.path.join(BASE_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, filename)

        rows = Reservation.query.filter_by(
            user_id=user_id
        ).order_by(Reservation.start_time.asc()).all()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Reservation ID", "Lot Name", "Spot ID", "Vehicle Number", "Start Time", "End Time", "Status", "Total Cost"])
            for r in rows:
                writer.writerow([
                    r.id,
                    r.lot.prime_location_name if r.lot else "",
                    r.spot_id,
                    r.vehicle_number or "",
                    r.start_time.isoformat() if r.start_time else "",
                    r.end_time.isoformat() if r.end_time else "",
                    r.status,
                    r.total_cost or 0
                ])

        # email attachment logic stays same…
        try:
            msg = Message(
                subject="Your Parking History Export",
                recipients=[user.username]
            )
            msg.html = f"<p>Hi {user.name or user.username},</p><p>Your parking history export is attached.</p>"
            with open(filepath, "rb") as fh:
                msg.attach(filename, "text/csv", fh.read())
            mail.send(msg)
        except Exception as e:
            app.logger.exception("Failed to send CSV email: %s", e)
            return {"error": str(e)}

        return {"status": "done", "filepath": filepath}

@app.route('/api/user/export/<string:username>', methods=['POST'])
def export_user_history(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    # Enqueue Celery job
    task = task_generate_csv_and_email.delay(user.id)
    return jsonify({"message": "Export started", "task_id": task.id}), 202

# -----------------------
# Celery tasks for daily reminders and monthly report
# -----------------------
@celery.task(name='tasks.send_daily_reminder')
def send_daily_reminder(user_id=None):
    with app.app_context():
        today = datetime.now(IST).date()

        # If testing specific user
        if user_id:
            user = User.query.get(user_id)
            if not user:
                # user not found → send to fallback email
                msg = Message(
                    subject="Daily Parking Reminder (Fallback)",
                    recipients=[MAIL_RECIVER]
                )
                msg.html = f"""
                <p>Requested user_id {user_id} not found.</p>
                <p>Sending this reminder to fallback email instead.</p>
                """
                mail.send(msg)
                return {"sent": 1, "fallback": True}

            # Skip admin user in specific test
            if user.role == "admin":
                return {"sent": 0, "skipped": "admin"}

            users = [user]

        else:
            users = User.query.all()

        sent = 0

        for user in users:
            if not user:
                continue

            # 🚫 Skip admins
            if user.role == "admin":
                continue

            latest = Reservation.query.filter_by(user_id=user.id) \
                .order_by(Reservation.start_time.desc()).first()

            no_booking_today = (
                latest is None
                or latest.start_time is None
                or latest.start_time.date() != today
            )

            if no_booking_today:
                try:
                    # If email missing → fallback
                    recipient = user.username if user.username else MAIL_RECIVER

                    html = f"""
                    <p>Hi {user.name or user.username},</p>
                    <p>This is a friendly reminder: we didn’t find a parking booking for you today.</p>
                    <p>If you need parking, please visit the app and reserve a spot.</p>
                    <p>Regards,<br/>Parking System</p>
                    """

                    msg = Message(
                        subject="Daily Parking Reminder",
                        recipients=[recipient]
                    )
                    msg.html = html
                    mail.send(msg)

                    sent += 1
                except Exception:
                    app.logger.exception("Failed to send daily reminder to %s", user.username)

        return {"sent": sent}

@celery.task(name='tasks.send_monthly_report')
def send_monthly_report(user_id=None):
    with app.app_context():
        now = datetime.now(IST)
        start_date = now - timedelta(days=30)
        end_date = now

        # If testing specific user
        if user_id:
            user = User.query.get(user_id)
            if not user:
                msg = Message(
                    subject="Parking Report (Fallback)",
                    recipients=[MAIL_RECIVER]
                )
                msg.html = f"""
                <p>Requested user_id {user_id} not found.</p>
                <p>Sending the monthly report to the fallback email instead.</p>
                """
                mail.send(msg)
                return {"sent": 1, "fallback": True}

            # Skip admin during specific test
            if user.role == "admin":
                return {"sent": 0, "skipped": "admin"}

            users = [user]

        else:
            users = User.query.all()

        sent = 0

        for user in users:
            if not user:
                continue

            # 🚫 Skip admin users
            if user.role == "admin":
                continue

            try:
                reservations = Reservation.query.filter(
                    Reservation.user_id == user.id,
                    Reservation.start_time >= start_date,
                    Reservation.start_time <= end_date
                ).all()

                total_spent = sum(r.total_cost or 0 for r in reservations)
                total_bookings = len(reservations)

                lot_count = {}
                for r in reservations:
                    name = (
                        r.lot.prime_location_name
                        if r.lot and r.lot.prime_location_name
                        else "Unknown"
                    )
                    lot_count[name] = lot_count.get(name, 0) + 1

                most_used = max(lot_count, key=lot_count.get) if lot_count else "None"

                recipient = user.username if user.username else MAIL_RECIVER

                html = f"""
                <h3>Parking Report (Last 30 Days)</h3>
                <p>Hi {user.name or user.username},</p>
                <p>Period: {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}</p>
                <table border="0" cellpadding="6" cellspacing="0">
                  <tr><td><b>Total bookings</b></td><td>{total_bookings}</td></tr>
                  <tr><td><b>Most used parking lot</b></td><td>{most_used}</td></tr>
                  <tr><td><b>Total amount spent</b></td><td>₹{total_spent}</td></tr>
                </table>
                <p>Thanks for using the Parking System!</p>
                """

                msg = Message(
                    subject="Your Parking Report (Last 30 Days)",
                    recipients=[recipient]
                )
                msg.html = html
                mail.send(msg)

                sent += 1

            except Exception:
                app.logger.exception(
                    "Failed to send monthly report to %s", user.username
                )

        return {"sent": sent}

# -----------------------
# Dummy Payment Portal
# -----------------------
@app.route('/api/payment/initiate', methods=['POST'])
def initiate_payment():
    data = request.get_json()
    reservation_id = data.get("reservation_id")

    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({"message": "Reservation not found"}), 404
    
    if not reservation.total_cost:
        return jsonify({"message": "Total cost not calculated"}), 400

    # Generate dummy payment URL
    dummy_url = f"http://localhost:5173/payment?amount={reservation.total_cost}&reservation_id={reservation_id}"

    return jsonify({
        "message": "Payment required",
        "amount": reservation.total_cost,
        "payment_url": dummy_url
    })

@app.route('/api/payment/confirm', methods=['POST'])
def confirm_payment():
    data = request.get_json()
    reservation_id = data.get("reservation_id")

    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({"message": "Reservation not found"}), 404

    return jsonify({
        "message": "Payment successful!",
        "reservation_id": reservation_id,
        "amount": reservation.total_cost
    })

# -----------------------
# Run
# -----------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('FLASK_DEBUG', 'True') == 'True', host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
