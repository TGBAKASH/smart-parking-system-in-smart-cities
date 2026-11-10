"""
Parking Space Model - ALL TIMES IN IST
"""

from datetime import datetime
from bson.objectid import ObjectId
import pytz

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

def now_ist():
    """Get current time in IST"""
    return datetime.now(IST)

class ParkingSpace:
    """Parking space model for managing parking listings"""
    
    VEHICLE_TYPES = ['2-wheeler', '4-wheeler', '4+wheeler']
    STATUSES = ['pending', 'approved', 'rejected', 'inactive']
    
    @staticmethod
    def create(db, owner_id, data):
        """Create a new parking space listing"""
        print(f"🏗️ Creating parking with owner_id: {owner_id}")
        print(f"📝 Owner_id type: {type(owner_id)}")
        
        # Parse datetime strings - handle both local and ISO formats
        def parse_datetime(dt_string):
            """Parse datetime from various formats"""
            if not dt_string:
                raise ValueError("DateTime string is required")
            
            # Remove 'Z' if present and replace with +00:00
            dt_string = dt_string.replace('Z', '+00:00')
            
            # If no timezone info, treat as UTC
            if '+' not in dt_string and '-' not in dt_string[-6:]:
                # Local datetime from browser
                return datetime.fromisoformat(dt_string)
            else:
                # ISO format with timezone
                return datetime.fromisoformat(dt_string)
        
        # Get vehicle type for this parking
        vehicle_type = data.get('vehicle_type', '2-wheeler')
        
        # Get pricing based on vehicle type
        # If price_per_hour exists (old format), use it for backward compatibility
        if 'price_per_hour' in data:
            # Old format - single price
            pricing = {
                '2-wheeler': float(data['price_per_hour']),
                '4-wheeler': float(data['price_per_hour']),
                '4+wheeler': float(data['price_per_hour'])
            }
        else:
            # New format - vehicle-specific pricing
            pricing = {
                '2-wheeler': float(data.get('price_2wheeler', 0)),
                '4-wheeler': float(data.get('price_4wheeler', 0)),
                '4+wheeler': float(data.get('price_4plus', 0))
            }
        
        parking_data = {
            'owner_id': ObjectId(owner_id),
            'title': data['title'],
            'description': data.get('description', ''),
            'address': data['address'],
            'location': {
                'type': 'Point',
                'coordinates': [float(data['longitude']), float(data['latitude'])]
            },
            'location_link': data.get('location_link', ''),  # Store the Google Maps link as-is
            'owner_name': data.get('owner_name', ''),
            'owner_phone': data.get('owner_phone', ''),
            'vehicle_type': vehicle_type,  # What vehicle type this parking is FOR
            'pricing': pricing,  # Pricing for each vehicle type
            'price_per_hour': pricing.get(vehicle_type, 0),  # Default price (for backward compatibility)
            'total_hours': int(data['total_hours']),
            'available_from': parse_datetime(data['available_from']),
            'available_to': parse_datetime(data['available_to']),
            'images': data.get('images', []),
            'amenities': data.get('amenities', []),
            'instructions': data.get('instructions', ''),
            'payment_methods': data.get('payment_methods', ['cash']),
            'upi_id': data.get('upi_id', ''),  # Store UPI ID (only shown after booking accepted)
            'status': 'pending',
            'is_available': True,
            'total_spaces': int(data.get('total_spaces', 1)),
            'available_spaces': int(data.get('total_spaces', 1)),
            'rating': 0.0,
            'total_reviews': 0,
            'total_bookings': 0,
            'created_at': now_ist().replace(tzinfo=None),
            'updated_at': now_ist().replace(tzinfo=None)
        }
        
        print(f"✅ Parking data prepared with owner_id: {parking_data['owner_id']}")
        print(f"📦 Full parking_data keys: {list(parking_data.keys())}")
        
        result = db.insert_one('parking_spaces', parking_data)
        print(f"🎉 Parking created with ID: {result}")
        return result
    
    @staticmethod
    def get_by_id(db, parking_id):
        """Get parking space by ID"""
        try:
            return db.find_one('parking_spaces', {'_id': ObjectId(parking_id)})
        except:
            return None
    
    @staticmethod
    def get_by_owner(db, owner_id, status=None):
        """Get all parking spaces owned by a user"""
        query = {'owner_id': ObjectId(owner_id)}
        if status:
            query['status'] = status
        
        return db.find_many('parking_spaces', query, sort=[('created_at', -1)])
    
    @staticmethod
    def search(db, filters):
        """Search parking spaces with filters"""
        query = {'status': 'approved', 'is_available': True}
        
        # CRITICAL: Filter out expired parking spaces
        # Only show parking where available_to (end date) is in the future
        from datetime import datetime
        import pytz
        
        # Use IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        
        # Make current_time naive (remove timezone) for MongoDB comparison
        # MongoDB stores naive datetime, so we need to compare with naive datetime
        current_time_naive = current_time.replace(tzinfo=None)
        query['available_to'] = {'$gte': current_time_naive}
        
        # City filter - CRITICAL for location-based search
        if filters.get('city'):
            # Case-insensitive city search in address field
            query['$or'] = [
                {'city': {'$regex': filters['city'], '$options': 'i'}},
                {'address': {'$regex': filters['city'], '$options': 'i'}}
            ]
        
        # Location-based search (coordinates)
        if filters.get('latitude') and filters.get('longitude'):
            max_distance = filters.get('radius', 5000)  # Default 5km
            query['location'] = {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [float(filters['longitude']), float(filters['latitude'])]
                    },
                    '$maxDistance': max_distance
                }
            }
        
        # Vehicle type filter
        if filters.get('vehicle_type'):
            # Need to handle $or carefully if city filter already added it
            vehicle_filter = [
                {'vehicle_type': filters['vehicle_type']},
                {'vehicle_type': 'both'}
            ]
            
            # If city filter already added $or, combine them
            if '$or' in query:
                # Move city filter to $and and add vehicle filter
                city_filter = query.pop('$or')
                query['$and'] = [
                    {'$or': city_filter},
                    {'$or': vehicle_filter}
                ]
            else:
                query['$or'] = vehicle_filter
        
        # Price range filter
        if filters.get('max_price'):
            query['price_per_hour'] = {'$lte': float(filters['max_price'])}
        
        # Date/time availability filter
        if filters.get('start_time') and filters.get('end_time'):
            start = datetime.fromisoformat(filters['start_time'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(filters['end_time'].replace('Z', '+00:00'))
            query['available_from'] = {'$lte': start}
            query['available_to'] = {'$gte': end}
        
        return db.find_many('parking_spaces', query, limit=filters.get('limit', 50))
    
    @staticmethod
    def update(db, parking_id, update_data):
        """Update parking space information"""
        # Remove fields that shouldn't be updated directly
        fields_to_remove = ['_id', 'owner_id', 'rating', 'total_reviews', 'total_bookings', 'created_at']
        for field in fields_to_remove:
            update_data.pop(field, None)
        
        # Always update the updated_at timestamp
        update_data['updated_at'] = now_ist().replace(tzinfo=None)
        
        print(f"💾 Updating parking {parking_id} with fields: {list(update_data.keys())}")
        
        result = db.update_one(
            'parking_spaces',
            {'_id': ObjectId(parking_id)},
            {'$set': update_data}
        )
        
        print(f"✅ Update matched: {result.matched_count}, modified: {result.modified_count}")
        return result
    
    @staticmethod
    def update_status(db, parking_id, status):
        """Update parking space status"""
        if status not in ParkingSpace.STATUSES:
            raise ValueError(f"Invalid status. Must be one of {ParkingSpace.STATUSES}")
        
        return db.update_one(
            'parking_spaces',
            {'_id': ObjectId(parking_id)},
            {'$set': {
                'status': status,
                'updated_at': now_ist().replace(tzinfo=None)
            }}
        )
    
    @staticmethod
    def update_availability(db, parking_id, change):
        """Update available spaces count"""
        parking = ParkingSpace.get_by_id(db, parking_id)
        if not parking:
            return False
        
        new_available = parking['available_spaces'] + change
        if new_available < 0 or new_available > parking['total_spaces']:
            return False
        
        return db.update_one(
            'parking_spaces',
            {'_id': ObjectId(parking_id)},
            {'$set': {
                'available_spaces': new_available,
                'is_available': new_available > 0,
                'updated_at': now_ist().replace(tzinfo=None)
            }}
        )
    
    @staticmethod
    def add_review(db, parking_id, rating):
        """Add a review and update average rating"""
        parking = ParkingSpace.get_by_id(db, parking_id)
        if not parking:
            return False
        
        total_reviews = parking.get('total_reviews', 0)
        current_rating = parking.get('rating', 0.0)
        
        new_total_reviews = total_reviews + 1
        new_rating = ((current_rating * total_reviews) + rating) / new_total_reviews
        
        return db.update_one(
            'parking_spaces',
            {'_id': ObjectId(parking_id)},
            {'$set': {
                'rating': round(new_rating, 2),
                'total_reviews': new_total_reviews,
                'updated_at': now_ist().replace(tzinfo=None)
            }}
        )
    
    @staticmethod
    def get_all_pending(db):
        """Get all parking spaces pending approval"""
        return db.find_many(
            'parking_spaces',
            {'status': 'pending'},
            sort=[('created_at', -1)]
        )
    
    @staticmethod
    def to_dict(parking, include_sensitive=False):
        """Convert parking document to dictionary
        
        Args:
            parking: Parking document from database
            include_sensitive: Whether to include sensitive data like UPI ID (only for owners/bookings)
        """
        if not parking:
            return None
        
        result = {
            'id': str(parking['_id']),
            'owner_id': str(parking['owner_id']),
            'title': parking['title'],
            'description': parking.get('description', ''),
            'address': parking['address'],
            'latitude': parking['location']['coordinates'][1],
            'longitude': parking['location']['coordinates'][0],
            'location_link': parking.get('location_link', ''),
            'owner_name': parking.get('owner_name', ''),
            'owner_phone': parking.get('owner_phone', ''),
            'vehicle_type': parking['vehicle_type'],
            'price_per_hour': parking['price_per_hour'],
            'total_hours': parking['total_hours'],
            'available_from': parking['available_from'].isoformat() if hasattr(parking['available_from'], 'isoformat') else parking['available_from'],
            'available_to': parking['available_to'].isoformat() if hasattr(parking['available_to'], 'isoformat') else parking['available_to'],
            'images': parking.get('images', []),
            'amenities': parking.get('amenities', []),
            'instructions': parking.get('instructions', ''),
            'payment_methods': parking.get('payment_methods', ['cash']),
            'status': parking['status'],
            'is_available': parking['is_available'],
            'total_spaces': parking['total_spaces'],
            'available_spaces': parking['available_spaces'],
            'rating': parking.get('rating', 0.0),
            'total_reviews': parking.get('total_reviews', 0),
            'total_bookings': parking.get('total_bookings', 0),
            'is_parking_a': parking.get('is_parking_a', False),
            'created_at': parking['created_at'].isoformat() if hasattr(parking['created_at'], 'isoformat') else parking['created_at'],
            'updated_at': parking['updated_at'].isoformat() if hasattr(parking['updated_at'], 'isoformat') else parking['updated_at'],
            # Edit tracking fields
            'is_edited': parking.get('is_edited', False),
            'edited_at': parking['edited_at'].isoformat() if parking.get('edited_at') and hasattr(parking['edited_at'], 'isoformat') else parking.get('edited_at'),
            'previous_status': parking.get('previous_status')
        }
        
        # Only include UPI ID if specifically requested (for bookings/owner view)
        if include_sensitive:
            result['upi_id'] = parking.get('upi_id', '')
        
        return result
