# (Python code for Flask app with Twilio, login, live tracking, etc.)
# Will be written in next step for brevity
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from twilio.rest import Client

app = Flask(__name__)
CORS(app)
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY", "mysecretkey")

# Twilio config
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# In-memory data
users = {}
emergency_contacts = {}
location_data = {}

@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users:
            return "User already exists."
        users[email] = password
        emergency_contacts[email] = []
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if users.get(email) == password:
            session['user'] = email
            return redirect(url_for('home'))
        else:
            return "Invalid credentials."
    return render_template('index.html')

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        emergency_contacts[user].append({'name': name, 'phone': phone})
    return render_template('contacts.html', contacts=emergency_contacts.get(user, []))

@app.route('/location', methods=['GET', 'POST'])
def location():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        data = request.get_json()
        location_data[user] = {
            'latitude': data['latitude'],
            'longitude': data['longitude']
        }
        return jsonify({'message': 'Location updated'})
    return render_template('live_location.html')

@app.route('/send-sos', methods=['POST'])
def send_sos():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    user_location = location_data.get(user)
    user_contacts = emergency_contacts.get(user, [])

    if not user_location:
        return "Location not available."

    message_body = f"SOS! I need help. Here's my location: https://www.google.com/maps?q={user_location['latitude']},{user_location['longitude']}"

    for contact in user_contacts:
        try:
            twilio_client.messages.create(
                body=message_body,
                from_=TWILIO_PHONE_NUMBER,
                to=contact['phone']
            )
        except Exception as e:
            print(f"Error sending SMS to {contact['phone']}: {e}")

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
