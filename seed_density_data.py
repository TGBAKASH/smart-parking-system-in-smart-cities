"""
Seed Script: Generate False Density Data with Random Forest Training Baseline
- Parking A: 100 bookings (High Density / Peak Traffic Surge)
- Parking B, C, D: <= 10 bookings (Low Density / High Availability)
"""

import os
import sys
import random
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import json

# Add current path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from utils.timezone import now_ist, IST

AREAS = [
    {
        'key': 'A',
        'title': 'Parking Space A - Central Metro Hub',
        'address': 'MG Road, Central Business District, Metro Station Gate 2',
        'latitude': 12.9716,
        'longitude': 77.5946,
        'price_per_hour': 50,
        'total_spaces': 120,
        'available_spaces': 20,
        'target_bookings': 100,
        'is_parking_a': True,
        'vehicle_type': '4-wheeler'
    },
    {
        'key': 'B',
        'title': 'Parking Space B - North Station Plaza',
        'address': 'Platform Road, North Terminal Junction',
        'latitude': 12.9850,
        'longitude': 77.6050,
        'price_per_hour': 40,
        'total_spaces': 40,
        'available_spaces': 32,
        'target_bookings': 8,
        'is_parking_a': False,
        'vehicle_type': '4-wheeler'
    },
    {
        'key': 'C',
        'title': 'Parking Space C - West Avenue Market',
        'address': '14th Cross, West Commercial Street',
        'latitude': 12.9620,
        'longitude': 77.5800,
        'price_per_hour': 35,
        'total_spaces': 30,
        'available_spaces': 24,
        'target_bookings': 6,
        'is_parking_a': False,
        'vehicle_type': '2-wheeler'
    },
    {
        'key': 'D',
        'title': 'Parking Space D - Green Tech Park',
        'address': 'Phase 1, Ring Road Tech Corridor',
        'latitude': 12.9350,
        'longitude': 77.6900,
        'price_per_hour': 30,
        'total_spaces': 50,
        'available_spaces': 46,
        'target_bookings': 4,
        'is_parking_a': False,
        'vehicle_type': '4-wheeler'
    }
]

def seed_mongo(db):
    """Seed data directly into MongoDB"""
    if db is None:
        return
    now = datetime.now(IST)
    
    # 1. Ensure host user
    host_user = db.users.find_one({'email': 'demohost@parksense.com'})
    if not host_user:
        from werkzeug.security import generate_password_hash
        host_data = {
            'email': 'demohost@parksense.com',
            'name': 'ParkSense Official Host',
            'password_hash': generate_password_hash('host123'),
            'phone': '9876543210',
            'role': 'user',
            'is_active': True,
            'created_at': now.replace(tzinfo=None)
        }
        host_id = db.users.insert_one(host_data).inserted_id
    else:
        host_id = host_user['_id']

    # 2. Ensure driver user
    driver_user = db.users.find_one({'email': 'demodriver@parksense.com'})
    if not driver_user:
        from werkzeug.security import generate_password_hash
        driver_data = {
            'email': 'demodriver@parksense.com',
            'name': 'Active Driver',
            'password_hash': generate_password_hash('driver123'),
            'phone': '9876543211',
            'role': 'user',
            'is_active': True,
            'created_at': now.replace(tzinfo=None)
        }
        driver_id = db.users.insert_one(driver_data).inserted_id
    else:
        driver_id = driver_user['_id']

    for item in AREAS:
        existing = db.parking_spaces.find_one({'title': item['title']})
        space_id = None
        # Valid until next year so never expires
        future_to = (now + timedelta(days=365)).replace(tzinfo=None)
        past_from = (now - timedelta(days=30)).replace(tzinfo=None)
        
        if existing:
            space_id = existing['_id']
            db.parking_spaces.update_one(
                {'_id': space_id},
                {'$set': {
                    'total_bookings': item['target_bookings'],
                    'status': 'approved',
                    'is_available': True,
                    'is_parking_a': item['is_parking_a'],
                    'available_spaces': item['available_spaces'],
                    'total_spaces': item['total_spaces'],
                    'available_from': past_from,
                    'available_to': future_to
                }}
            )
        else:
            doc = {
                'owner_id': ObjectId(host_id),
                'title': item['title'],
                'address': item['address'],
                'description': f"Smart parking space with automated gate and real-time monitoring at {item['title']}",
                'location': {
                    'type': 'Point',
                    'coordinates': [item['longitude'], item['latitude']]
                },
                'price_per_hour': item['price_per_hour'],
                'pricing': {
                    '2-wheeler': item['price_per_hour'] * 0.6,
                    '4-wheeler': item['price_per_hour'],
                    '4+wheeler': item['price_per_hour'] * 1.5
                },
                'total_hours': 24,
                'available_from': past_from,
                'available_to': future_to,
                'status': 'approved',
                'is_available': True,
                'is_parking_a': item['is_parking_a'],
                'vehicle_type': item['vehicle_type'],
                'total_spaces': item['total_spaces'],
                'available_spaces': item['available_spaces'],
                'total_bookings': item['target_bookings'],
                'rating': 4.8 if item['is_parking_a'] else 4.2,
                'total_reviews': 32 if item['is_parking_a'] else 4,
                'created_at': past_from,
                'updated_at': now.replace(tzinfo=None)
            }
            res = db.parking_spaces.insert_one(doc)
            space_id = res.inserted_id

        # Check bookings count
        current_b_count = db.bookings.count_documents({'parking_id': ObjectId(space_id)})
        diff = item['target_bookings'] - current_b_count
        if diff > 0:
            booking_docs = []
            for i in range(diff):
                hours_ago = random.randint(1, 168)
                b_start = (now - timedelta(hours=hours_ago)).replace(tzinfo=None)
                b_duration = random.choice([1, 2, 3, 4])
                b_end = b_start + timedelta(hours=b_duration)
                booking_docs.append({
                    'user_id': ObjectId(driver_id),
                    'parking_id': ObjectId(space_id),
                    'owner_id': ObjectId(host_id),
                    'start_time': b_start,
                    'end_time': b_end,
                    'duration_hours': b_duration,
                    'price_per_hour': item['price_per_hour'],
                    'number_of_spots': 1,
                    'total_price': item['price_per_hour'] * b_duration,
                    'vehicle_type': item['vehicle_type'],
                    'status': random.choice(['confirmed', 'completed', 'active']),
                    'created_at': b_start,
                    'updated_at': b_start
                })
            if booking_docs:
                db.bookings.insert_many(booking_docs)

    print("[OK] MongoDB successfully synced with Parking A (100 bookings) and other spots (<= 10 bookings).")

def ensure_density_data_in_db(db):
    """Called automatically on app start: guarantees database is populated and active"""
    if db is None:
        return
    now = datetime.now(IST)
    existing_a = db.parking_spaces.find_one({'title': 'Parking Space A - Central Metro Hub'})
    # If not present or expired, seed immediately
    if not existing_a or existing_a.get('available_to', datetime.min) < now.replace(tzinfo=None):
        seed_mongo(db)

def generate_static_fallback():
    """Generates the static fallback file for offline resilience"""
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static', 'data'), exist_ok=True)
    json_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'density_data.json')

    from utils.ml_density import rf_density_engine
    now = datetime.now(IST)

    analytics_export = {
        'generated_at': now.isoformat(),
        'target_scenario': {
            'description': 'Parking A has 100 bookings (High Density), remaining parking spaces have <= 10 bookings',
            'parking_a_count': 100,
            'max_other_count': 10
        },
        'areas': [
            {
                'id': 'parking_a_demo',
                'name': 'Parking Space A (Central Metro Hub)',
                'short_name': 'Parking A',
                'bookings': 100,
                'total_spaces': 120,
                'price_per_hour': 50,
                'ai_prediction': rf_density_engine.predict_density(100, total_spaces=120, price=50),
                'share_percentage': round((100 / (100 + 8 + 6 + 4)) * 100, 1)
            },
            {
                'id': 'parking_b_demo',
                'name': 'Parking Space B (North Station Plaza)',
                'short_name': 'Parking B',
                'bookings': 8,
                'total_spaces': 40,
                'price_per_hour': 40,
                'ai_prediction': rf_density_engine.predict_density(8, total_spaces=40, price=40),
                'share_percentage': round((8 / (100 + 8 + 6 + 4)) * 100, 1)
            },
            {
                'id': 'parking_c_demo',
                'name': 'Parking Space C (West Avenue Market)',
                'short_name': 'Parking C',
                'bookings': 6,
                'total_spaces': 30,
                'price_per_hour': 35,
                'ai_prediction': rf_density_engine.predict_density(6, total_spaces=30, price=35),
                'share_percentage': round((6 / (100 + 8 + 6 + 4)) * 100, 1)
            },
            {
                'id': 'parking_d_demo',
                'name': 'Parking Space D (Green Tech Park)',
                'short_name': 'Parking D',
                'bookings': 4,
                'total_spaces': 50,
                'price_per_hour': 30,
                'ai_prediction': rf_density_engine.predict_density(4, total_spaces=50, price=30),
                'share_percentage': round((4 / (100 + 8 + 6 + 4)) * 100, 1)
            }
        ],
        'feature_importances': rf_density_engine.get_feature_importances(),
        'peak_summary': {
            'peak_area': 'Parking Space A (Central Metro Hub)',
            'peak_bookings': 100,
            'peak_density_level': 'High Density',
            'peak_confidence': 99.5,
            'non_peak_average': 6.0
        }
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analytics_export, f, indent=2)
    print(f"[OK] Generated static density baseline dataset at: {json_path}")

def run_seed():
    print("=" * 70)
    print("PARKSENSE SEEDING: FALSE DENSITY DATA GENERATION")
    print("=" * 70)
    db = None
    try:
        from pymongo import MongoClient
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        db = client.get_database()
        print(f"[OK] Connected to MongoDB: {db.name}")
        seed_mongo(db)
    except Exception as e:
        print(f"[INFO] MongoDB offline ({e}). Generating static fallback dataset.")

    generate_static_fallback()

if __name__ == '__main__':
    run_seed()
