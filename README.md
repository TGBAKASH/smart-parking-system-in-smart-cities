# 🚗 Smart City Peer-to-Peer (P2P) Parking System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%20v3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MongoDB-brightgreen.svg)](https://www.mongodb.com/)
[![Live App](https://img.shields.io/badge/Live_Web_App-smartcityparking.onrender.com-brightgreen)](https://smartcityparking.onrender.com)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

A decentralized, full-stack **Peer-to-Peer (P2P) Smart Parking Marketplace** designed for modern smart cities. The platform empowers space owners (Hosts) to monetize underutilized private driveways, residential garages, and vacant commercial spots, while enabling drivers to seamlessly search, reserve, navigate to, and pay for parking spots in real time.

🌐 **Live Application**: [https://smartcityparking.onrender.com](https://smartcityparking.onrender.com)

---

## 🌟 Key Highlights & P2P Architecture

In rapidly growing urban areas, traditional parking structures are overwhelmed, while thousands of private driveways and residential spaces remain empty during business hours. This project bridges that gap through a P2P sharing economy model:

* **Direct Peer-to-Peer Monetization**: Space owners list unused spots with custom hourly/daily pricing, availability windows, vehicle restrictions (2-wheeler, 4-wheeler, EV), and amenities.
* **Instant & Approval-Based Booking**: Drivers can instantly book spots or submit reservation requests requiring host confirmation.
* **Dual Payment Ecosystem**: Integrated support for traditional fiat payments (UPI, Credit/Debit cards via **Razorpay**) and Web3/Cryptocurrency payments via **NOWPayments**, paired with an in-app wallet system.
* **In-App P2P Chat**: Integrated real-time messaging between hosts and drivers to share check-in instructions, gate access codes, and arrival updates.
* **Zero-File-Dependency Media Engine**: Spot images are optimized and stored as Base64 strings directly in MongoDB, eliminating complex cloud storage dependencies (S3/Cloudinary) for effortless multi-cloud deployment.

---

## 🛠️ Technology Stack

### **Backend**
* **Language & Framework**: Python 3.10+, Flask 3.0
* **Authentication**: JWT (JSON Web Tokens via `Flask-JWT-Extended`)
* **Database**: MongoDB (via `PyMongo 4.6`)
* **WSGI Server**: Gunicorn

### **Frontend**
* **UI Templates**: HTML5, Jinja2, Custom Responsive CSS3, JavaScript (ES6+)
* **Interactive Maps**: Leaflet.js & Google Maps JavaScript API for geolocation and pin routing

### **Payments & Services**
* **Fiat Payments**: Razorpay API (UPI, Netbanking, Cards)
* **Crypto Payments**: NOWPayments API (BTC, ETH, USDT, etc.)
* **Security**: Password hashing via `werkzeug.security`

---

## 📁 Project Structure

```
smart-parking-system-in-smart-cities/
├── app.py                      # Main application entry point & factory setup
├── config.py                   # Centralized configuration & environment loader
├── requirements.txt            # Python dependencies
├── Procfile                    # Deployment execution command for Heroku/Render
├── render.yaml                 # Infrastructure as Code for Render deployment
├── runtime.txt                 # Python runtime version definition
├── webhook_handler.py          # Payment gateway webhook handler
├── models/                     # Database models & schema helpers
│   ├── database.py             # PyMongo client initialization
│   ├── user.py                 # User authentication & profile schema
│   ├── parking.py              # Parking spot listings & geo-indexes
│   ├── booking.py              # Booking lifecycle management
│   ├── wallet.py               # In-app wallet & balance operations
│   ├── message.py              # P2P messaging data model
│   └── review.py               # Peer ratings & reviews
├── routes/                     # Modular API Blueprints
│   ├── auth.py                 # Login, Registration, Profile routes
│   ├── parking.py              # Spot listing, geolocation search, CRUD
│   ├── booking.py              # Reservations, requests, status updates
│   ├── payment.py              # Razorpay & NOWPayments initialization
│   ├── payment_razorpay.py     # Razorpay specific hooks
│   ├── payment_nowpayments.py  # NOWPayments crypto handler
│   ├── wallet.py               # In-app wallet deposits/withdrawals
│   ├── chat.py                 # Host-Driver P2P messaging API
│   ├── review.py               # Ratings and comments
│   ├── admin.py                # Platform admin analytics & moderation
│   └── web.py                  # Frontend web page routes
├── templates/                  # Responsive HTML5 UI templates
│   ├── index.html              # Landing page
│   ├── login.html / register.html
│   ├── dashboard.html          # User dashboard (Driver & Host views)
│   ├── find-parking.html       # Interactive spot map & search
│   ├── list-space.html         # Host spot listing creator
│   ├── booking.html            # Reservation checkout & details
│   ├── booking-requests.html   # Host approval dashboard
│   ├── my-bookings.html        # Driver booking history
│   └── admin.html              # System administration portal
└── static/                     # CSS, JS assets, and images
```

---

## ⚡ Features Overview

### 1. 🚘 For Drivers
* **Geospatial Spot Search**: Find available parking spots near current location or target address within a specified radius.
* **Real-Time Reservation**: Reserve spots on-demand or schedule future arrival/departure times.
* **Multiple Vehicle Support**: Filter spots by Hatchback, Sedan, SUV, Bike/Scooter, or EV Charging status.
* **Flexible Payments**: Pay using UPI/Cards via Razorpay, Crypto, or prepaid In-App Wallet.
* **Live P2P Chat**: Direct messaging channel with space owners.
* **Reviews & Ratings**: Rate host hospitality, security, and space cleanliness.

### 2. 🏡 For Hosts (Parking Spot Owners)
* **Spot Monetization**: Set custom hourly or daily rental rates.
* **Flexible Approval Modes**: Choose between *Instant Booking* or *Manual Approval*.
* **Photo Upload**: Upload spot photos seamlessly (auto-converted to lightweight Base64).
* **Booking Request Manager**: View incoming booking requests, approve/reject, and monitor active parked vehicles.
* **Earnings & Payouts**: Track revenues in real time and request wallet withdrawals.

### 3. 🛡️ System & Admin Moderation
* **Admin Dashboard**: Comprehensive stats on active users, total listed spots, booking revenue, and transaction volume.
* **Listing Verification**: Approve or flag newly created parking listings for safety compliance.
* **User Management**: Manage host and driver accounts, ban bad actors, and handle dispute resolutions.

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.10 or higher
* MongoDB instance running locally (`mongodb://localhost:27017`) or a free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster.

### 1. Clone the Repository
```bash
git clone https://github.com/TGBAKASH/smart-parking-system-in-smart-cities.git
cd smart-parking-system-in-smart-cities
```

### 2. Set Up Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:

```env
# Server Config
SECRET_KEY=your_super_secret_flask_key
JWT_SECRET_KEY=your_jwt_signing_key

# MongoDB Connection
MONGO_URI=mongodb://localhost:27017/parking_system
# Or Atlas: MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/parking_system

# Third-Party APIs (Optional for basic local testing)
GOOGLE_MAPS_API_KEY=your_google_maps_key
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
NOWPAYMENTS_API_KEY=your_nowpayments_api_key
```

### 5. Run the Application
```bash
python app.py
```
The application will launch locally at `http://127.0.0.1:5000`.

---

## 🔌 API Endpoints Summary

| Module | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/auth/register` | Register driver or host account |
| **Auth** | `POST` | `/api/auth/login` | Authenticate & return JWT token |
| **Parking** | `GET` | `/api/parking/search` | Search spots by lat/lng & radius |
| **Parking** | `POST` | `/api/parking/add` | Host creates new parking listing |
| **Booking** | `POST` | `/api/booking/create` | Reserve a parking spot |
| **Booking** | `PUT` | `/api/booking/<id>/status` | Update booking status (`approve`/`cancel`/`complete`) |
| **Payment** | `POST` | `/api/payment/create-razorpay-order` | Initiate Razorpay checkout |
| **Payment** | `POST` | `/api/payment/create-nowpayments-invoice` | Initiate Crypto payment invoice |
| **Wallet** | `GET` | `/api/wallet/balance` | Retrieve user's wallet balance |
| **Chat** | `POST` | `/api/chat/send` | Send P2P message between Host & Driver |
| **Review** | `POST` | `/api/review/add` | Post host/spot rating and feedback |

---

## ☁️ Deployment

The project is pre-configured for instant one-click deployment on **Render**, **Heroku**, or **AWS**:

* **Render**: Includes `render.yaml`. Connect your GitHub repository to Render Web Service, add your `.env` variables, and deploy automatically.
* **Gunicorn**: Production command:
  ```bash
  gunicorn app:app
  ```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
