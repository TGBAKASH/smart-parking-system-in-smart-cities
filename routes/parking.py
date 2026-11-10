"""
Parking Space Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.parking import ParkingSpace
from utils.ml_density import rf_density_engine
from models.user import User
from models.review import Review
from models.database import db as database
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

parking_bp = Blueprint('parking', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@parking_bp.route('/create', methods=['POST'])
@jwt_required()
def create_parking():
    """Create a new parking space listing"""
    try:
        user_id = get_jwt_identity()
        
        # Verify database is initialized
        if database.db is None:
            return jsonify({'error': 'Database not initialized. Please contact support.'}), 500
        
        # Verify user exists
        user = User.get_by_id(database, user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found. Your session may have expired. Please log in again.'
            }), 404
        
        # Any user can list a parking space (become a host)
        data = request.get_json()
        
        # Log the received data for debugging
        print(f"Received parking data: {data}")
        
        # Validate required fields
        required_fields = ['title', 'address', 'latitude', 'longitude', 
                          'price_per_hour', 'total_hours', 'available_from', 'available_to']
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Create parking space
        parking_id = ParkingSpace.create(database, user_id, data)
        
        # Get created parking space
        parking = ParkingSpace.get_by_id(database, str(parking_id))
        
        return jsonify({
            'message': 'Parking space created successfully. Pending admin approval.',
            'parking': ParkingSpace.to_dict(parking)
        }), 201
        
    except ValueError as e:
        print(f"ValueError in parking creation: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Exception in parking creation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to create parking space: {str(e)}'}), 500

@parking_bp.route('/upload-image', methods=['POST'])
@jwt_required()
def upload_image():
    """Upload parking space image - stores as base64 in MongoDB"""
    try:
        user_id = get_jwt_identity()
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif'}), 400
        
        # Read file as bytes
        file_bytes = file.read()
        
        # Convert to base64
        import base64
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        
        # Get file extension
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        
        # Create data URL
        mime_type = f"image/{file_ext}"
        if file_ext == 'jpg':
            mime_type = 'image/jpeg'
        
        image_data_url = f"data:{mime_type};base64,{base64_image}"
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'url': image_data_url  # Returns data URL that works anywhere
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to upload image', 'details': str(e)}), 500

@parking_bp.route('/search', methods=['GET'])
def search_parking():
    """Search parking spaces with filters"""
    try:
        filters = {
            'city': request.args.get('city'),  # Add city filter
            'latitude': request.args.get('latitude'),
            'longitude': request.args.get('longitude'),
            'radius': request.args.get('radius', 5000),  # Default 5km
            'vehicle_type': request.args.get('vehicle_type'),
            'max_price': request.args.get('max_price'),
            'start_time': request.args.get('start_time'),
            'end_time': request.args.get('end_time'),
            'limit': int(request.args.get('limit', 50))
        }
        
        parking_spaces = []
        if database.db is not None:
            try:
                parking_spaces = ParkingSpace.search(database, filters)
            except Exception as e:
                print(f"Error querying parking_spaces: {e}")
        
        # Add remaining hours calculation for each parking space
        from datetime import datetime
        import pytz
        
        # Use IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        
        spaces_with_time = []
        for p in parking_spaces:
            space_dict = ParkingSpace.to_dict(p)
            space_dict = rf_density_engine.enrich_parking_space(space_dict)
            
            # Calculate remaining hours from now until available_to
            available_to = p['available_to']
            
            # If available_to is naive (no timezone), assume it's IST
            if available_to.tzinfo is None:
                available_to = ist.localize(available_to)
            else:
                # Convert to IST if it has a different timezone
                available_to = available_to.astimezone(ist)
            
            # Make current_time offset-aware if needed for comparison
            if current_time.tzinfo is None:
                current_time = ist.localize(current_time)
            
            if available_to > current_time:
                remaining_seconds = (available_to - current_time).total_seconds()
                remaining_hours = max(0, remaining_seconds / 3600)
                space_dict['remaining_hours'] = round(remaining_hours, 1)
                space_dict['min_booking_hours'] = round(remaining_hours * 0.7, 1)
            else:
                # Expired parking (shouldn't happen due to search filter, but safety check)
                space_dict['remaining_hours'] = 0
                space_dict['min_booking_hours'] = 0
            
            spaces_with_time.append(space_dict)
        
        if not spaces_with_time:
            # Fallback to seed density data to support demonstration in local/offline modes
            import json
            json_file = os.path.join(current_app.root_path, 'static', 'data', 'density_data.json')
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as jf:
                        mock_data = json.load(jf)
                        demo_spaces = []
                        for item in mock_data.get('areas', []):
                            sp = {
                                'id': item['id'],
                                'title': item['name'],
                                'address': 'Smart City Zone - Hub ' + item['short_name'],
                                'price_per_hour': item.get('price_per_hour', 40),
                                'total_spaces': item.get('total_spaces', 50),
                                'available_spaces': max(2, item.get('total_spaces', 50) - item['bookings']),
                                'total_hours': 24,
                                'remaining_hours': 18.0,
                                'vehicle_type': '4-wheeler',
                                'status': 'approved',
                                'is_available': True,
                                'total_bookings': item['bookings'],
                                'ai_density': item['ai_prediction'],
                                'images': []
                            }
                            demo_spaces.append(sp)
                        return jsonify({
                            'count': len(demo_spaces),
                            'parking_spaces': demo_spaces
                        }), 200
                except Exception as ex:
                    print(f"Fallback error: {ex}")

        return jsonify({
            'count': len(spaces_with_time),
            'parking_spaces': spaces_with_time
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

@parking_bp.route('/<parking_id>', methods=['GET'])
def get_parking_details(parking_id):
    """Get parking space details"""
    try:
        print(f"Fetching parking details for ID: {parking_id}")
        
        # Validate parking_id format
        from bson.objectid import ObjectId
        from bson.errors import InvalidId
        
        try:
            ObjectId(parking_id)
        except (InvalidId, TypeError) as e:
            print(f"Invalid parking ID format: {parking_id}")
            return jsonify({'error': 'Invalid parking ID format'}), 400
        
        parking = ParkingSpace.get_by_id(database, parking_id)
        
        if not parking:
            print(f"Parking space not found: {parking_id}")
            return jsonify({'error': 'Parking space not found'}), 404
        
        print(f"Parking found: {parking.get('title', 'N/A')}")
        
        # Get owner details
        try:
            owner = User.get_by_id(database, str(parking['owner_id']))
            if not owner:
                print(f"Owner not found for parking: {parking_id}")
                return jsonify({'error': 'Parking owner not found'}), 404
        except Exception as e:
            print(f"Error fetching owner: {str(e)}")
            return jsonify({'error': 'Failed to fetch owner details', 'details': str(e)}), 500
        
        # Get reviews (non-critical, can fail gracefully)
        try:
            reviews = Review.get_by_parking(database, parking_id, limit=10)
        except Exception as e:
            print(f"Error fetching reviews (non-critical): {str(e)}")
            reviews = []
        
        response_data = {
            'parking': ParkingSpace.to_dict(parking),
            'owner': {
                'id': str(owner['_id']),
                'name': owner['name'],
                'email': owner['email']
            },
            'reviews': [Review.to_dict(r) for r in reviews]
        }
        
        # Add remaining hours calculation
        from datetime import datetime
        import pytz
        
        # Use IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        available_to = parking['available_to']
        
        # If available_to is naive (no timezone), assume it's IST
        if available_to.tzinfo is None:
            available_to = ist.localize(available_to)
        else:
            # Convert to IST if it has a different timezone
            available_to = available_to.astimezone(ist)
        
        # Make current_time offset-aware if needed for comparison
        if current_time.tzinfo is None:
            current_time = ist.localize(current_time)
        
        if available_to > current_time:
            remaining_seconds = (available_to - current_time).total_seconds()
            remaining_hours = max(0, remaining_seconds / 3600)
            response_data['parking']['remaining_hours'] = round(remaining_hours, 1)
            response_data['parking']['min_booking_hours'] = round(remaining_hours * 0.7, 1)
        else:
            response_data['parking']['remaining_hours'] = 0
            response_data['parking']['min_booking_hours'] = 0
        
        print(f"Successfully returning parking details for: {parking_id}")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Unexpected error in get_parking_details: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get parking details', 'details': str(e)}), 500

@parking_bp.route('/my-listings', methods=['GET'])
@jwt_required()
def get_my_listings():
    """Get user's parking listings"""
    try:
        user_id = get_jwt_identity()
        status = request.args.get('status')
        
        print(f"🔍 Getting listings for user_id: {user_id}")
        print(f"📝 User_id type: {type(user_id)}")
        print(f"🔑 Converting to ObjectId: {ObjectId(user_id)}")
        
        parking_spaces = ParkingSpace.get_by_owner(database, user_id, status)
        
        print(f"✅ Found {len(parking_spaces)} parkings for user {user_id}")
        
        if len(parking_spaces) > 0:
            print(f"📦 First parking owner_id: {parking_spaces[0].get('owner_id')}")
        
        # Also check ALL parkings to debug
        all_parkings = database.find_many('parking_spaces', {})
        print(f"🌐 Total parkings in DB: {len(all_parkings)}")
        if len(all_parkings) > 0:
            for p in all_parkings[-3:]:  # Show last 3
                print(f"  - Parking {p.get('_id')}: owner_id={p.get('owner_id')}, title={p.get('title')}")
        
        return jsonify({
            'count': len(parking_spaces),
            'parking_spaces': [ParkingSpace.to_dict(p) for p in parking_spaces]
        }), 200
        
    except Exception as e:
        print(f"❌ Error in get_my_listings: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get listings', 'details': str(e)}), 500

@parking_bp.route('/<parking_id>', methods=['PUT'])
@jwt_required()
def update_parking(parking_id):
    """Update parking space - requires admin re-approval"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user owns this parking space
        parking = ParkingSpace.get_by_id(database, parking_id)
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        if str(parking['owner_id']) != user_id:
            return jsonify({'error': 'You do not have permission to update this parking space'}), 403
        
        # Check if there are any active bookings for this parking
        active_bookings = database.find_many('bookings', {
            'parking_id': ObjectId(parking_id),
            'status': {'$in': ['pending', 'confirmed', 'active']}
        })
        
        if len(active_bookings) > 0:
            return jsonify({
                'error': 'Cannot edit parking',
                'message': f'This parking has {len(active_bookings)} active booking(s). You cannot edit while bookings are active.'
            }), 400
        
        data = request.get_json()
        
        # CRITICAL: Parse datetime strings to datetime objects
        # Without this, available_from/available_to get stored as strings in MongoDB,
        # breaking the $gte datetime comparison in search queries (listings disappear from dashboard)
        if 'available_from' in data and isinstance(data['available_from'], str):
            dt_string = data['available_from'].replace('Z', '+00:00')
            data['available_from'] = datetime.fromisoformat(dt_string)
        if 'available_to' in data and isinstance(data['available_to'], str):
            dt_string = data['available_to'].replace('Z', '+00:00')
            data['available_to'] = datetime.fromisoformat(dt_string)
        
        print(f"🔧 Updating parking {parking_id}")
        print(f"📝 Incoming data: {data}")
        print(f"📊 Current parking status: {parking.get('status')}, is_available: {parking.get('is_available')}")
        
        # Preserve critical fields that shouldn't change
        data.pop('_id', None)
        data.pop('owner_id', None)
        data.pop('rating', None)
        data.pop('total_reviews', None)
        data.pop('total_bookings', None)
        data.pop('created_at', None)
        
        # CRITICAL: Mark as edited and send back to pending for admin approval
        # Only if the parking was previously approved
        was_approved = parking.get('status') == 'approved'
        
        if was_approved:
            data['status'] = 'pending'  # Send back to admin for approval
            data['is_edited'] = True  # Flag to indicate this is an edit, not new listing
            data['previous_status'] = 'approved'  # Store previous status
            data['edited_at'] = datetime.utcnow()  # Track when it was edited
            print(f"⚠️ Parking was approved, sending back to pending for re-approval")
        else:
            # If already pending, just update and keep pending
            data['status'] = parking.get('status', 'pending')
            data['is_edited'] = parking.get('is_edited', False)
        
        # Preserve is_available and available_spaces (critical for showing on dashboard)
        data['is_available'] = parking['is_available']
        
        # CRITICAL FIX: Preserve available_spaces if not explicitly being updated
        if 'available_spaces' not in data and 'total_spaces' in data:
            # If total_spaces is being updated, set available_spaces accordingly
            # (assuming no bookings since we checked above)
            data['available_spaces'] = int(data['total_spaces'])
        elif 'available_spaces' not in data:
            # Preserve existing available_spaces
            data['available_spaces'] = parking['available_spaces']
        
        print(f"✅ Setting status: {data.get('status')}, is_edited: {data.get('is_edited')}")
        
        # Update parking space
        result = ParkingSpace.update(database, parking_id, data)
        print(f"📦 Update result - matched: {result.matched_count}, modified: {result.modified_count}")
        
        # Get updated parking space
        updated_parking = ParkingSpace.get_by_id(database, parking_id)
        print(f"🎉 Updated parking status: {updated_parking.get('status')}, is_edited: {updated_parking.get('is_edited')}")
        
        if not updated_parking:
            return jsonify({'error': 'Failed to retrieve updated parking'}), 500
        
        # Different message based on whether it needs re-approval
        if was_approved:
            message = 'Parking space updated successfully. Waiting for admin approval to go live again.'
        else:
            message = 'Parking space updated successfully.'
        
        return jsonify({
            'message': message,
            'needs_approval': was_approved,
            'parking': ParkingSpace.to_dict(updated_parking)
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating parking: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to update parking space', 'details': str(e)}), 500

@parking_bp.route('/<parking_id>', methods=['DELETE'])
@jwt_required()
def delete_parking(parking_id):
    """Delete/deactivate parking space"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user owns this parking space
        parking = ParkingSpace.get_by_id(database, parking_id)
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        if str(parking['owner_id']) != user_id:
            return jsonify({'error': 'You do not have permission to delete this parking space'}), 403
        
        # Deactivate instead of delete
        ParkingSpace.update_status(database, parking_id, 'inactive')
        
        return jsonify({
            'message': 'Parking space deactivated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete parking space', 'details': str(e)}), 500

@parking_bp.route('/<parking_id>/reviews', methods=['GET'])
def get_parking_reviews(parking_id):
    """Get reviews for a parking space"""
    try:
        reviews = Review.get_by_parking(database, parking_id)
        
        # Get user details for each review
        reviews_with_users = []
        for review in reviews:
            user = User.get_by_id(database, str(review['user_id']))
            review_dict = Review.to_dict(review)
            review_dict['user'] = {
                'name': user['name'],
                'profile_image': user.get('profile_image')
            }
            reviews_with_users.append(review_dict)
        
        return jsonify({
            'count': len(reviews_with_users),
            'reviews': reviews_with_users
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reviews', 'details': str(e)}), 500
