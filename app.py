# (Python code for Flask app with Twilio, login, live tracking, etc.)
# Will be written in next step for brevity
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from twilio.rest import Client
from dotenv import load_dotenv
import os



app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

# Twilio credentials from environment variables
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# In-memory database
users = {}

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users:
            return 'User already exists'
        users[email] = {'password': password, 'contacts': [], 'location': None}
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.get(email)
        if user and user['password'] == password:
            session['user'] = email
            return redirect(url_for('home'))
        return 'Invalid credentials'
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = users[session['user']]
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        user['contacts'].append({'name': name, 'phone': phone})
    return render_template('contacts.html', contacts=user['contacts'])

@app.route('/location', methods=['GET', 'POST'])
def location():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = users[session['user']]
    if request.method == 'POST':
        data = request.json
        user['location'] = {
            'latitude': data['latitude'],
            'longitude': data['longitude']
        }
        return jsonify({'message': 'Location updated successfully'})
    return render_template('live_location.html')

@app.route('/send-sos', methods=['POST'])
def send_sos():
    if 'user' not in session:
        return 'Unauthorized', 401
    user = users[session['user']]
    location = user.get('location')
    contacts = user.get('contacts', [])
    if not location:
        return jsonify({'error': 'No location available'}), 400
    message = (
        f"🚨 SOS Alert from {session['user']}!\n"
        f"Location: https://www.google.com/maps?q={location['latitude']},{location['longitude']}"
    )
    for contact in contacts:
        try:
            twilio_client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=contact['phone']
            )
        except Exception as e:
            print(f"Failed to send to {contact['phone']}: {e}")
    return jsonify({'message': 'SOS messages sent'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
