from flask import Flask, render_template, request, redirect, session, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SESSION_TYPE'] = 'filesystem'

db = SQLAlchemy(app)
Session(app)

class UserModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class BookingModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    time_slot = db.Column(db.String(100), nullable=False)

@app.route('/')
def index():
    return redirect('/login')

@app.route('/register', methods=['POST'])
def api_register():

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    is_admin = data.get("is_admin", False)

    hashed_pw = generate_password_hash(password)
    user = UserModel(username=username, password=hashed_pw, is_admin=is_admin)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created'}), 201

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']
        user = UserModel.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, pwd):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect('/booking')
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    is_admin = session['is_admin']

    if request.method == 'POST':
        time_slot = request.form['time_slot']
        new_booking = BookingModel(user_id=user_id, time_slot=time_slot)
        db.session.add(new_booking)
        db.session.commit()

    user_bookings = BookingModel.query.filter_by(user_id=user_id).all()

    all_bookings = {}
    if is_admin:
        all = BookingModel.query.all()
        for booking in all:
            user = UserModel.query.get(booking.user_id)
            all_bookings.setdefault(user.username, []).append(booking.time_slot)

    return render_template('bookings.html',
                           username=session['username'],
                           user_bookings=user_bookings,
                           is_admin=is_admin,
                           all_bookings=all_bookings)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
