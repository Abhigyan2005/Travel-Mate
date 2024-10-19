from flask import Flask, render_template, url_for, redirect, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Use relative path for SQLite
app.config['SECRET_KEY'] = 'thisisasecretkey'  # Flask session key for login handling

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Ensure this points to the login view

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

# Trip Model
class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    people = db.Column(db.String(100), nullable=False)
    money_required = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('trips', lazy=True))

# Flask Forms
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

class PlanYourTripForm(FlaskForm):
    location = StringField('Location', validators=[InputRequired()])
    people = StringField('Number of People', validators=[InputRequired()])
    money_required = StringField('Money Required', validators=[InputRequired()])
    description = TextAreaField('Description', validators=[InputRequired()])
    submit = SubmitField('Submit')

# Load User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to dashboard after login
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password)

        db.session.add(new_user)
        try:
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))  # Redirect to login after registration
        except Exception as e:
            db.session.rollback()
            flash('There was an error with your registration. Please try again.', 'danger')
            print("Error:", e)

    return render_template('register.html', form=form)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    search_query = request.args.get('search', '')

    if search_query:
        trips = Trip.query.join(User).filter(
            (Trip.location.ilike(f"%{search_query}%")) |
            (User.username.ilike(f"%{search_query}%"))
        ).all()
    else:
        trips = Trip.query.join(User).all()

    form = PlanYourTripForm()
    if form.validate_on_submit():
        new_trip = Trip(
            location=form.location.data,
            people=form.people.data,
            money_required=form.money_required.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(new_trip)
        db.session.commit()
        flash('Trip has been planned successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('dashboard.html', form=form, trips=trips)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out!', 'info')
    return redirect(url_for('home'))  # Redirect to home after logout

# Route to get trip details (in JSON format for use in JavaScript)
@app.route('/trip-details/<int:trip_id>', methods=['GET'])
@login_required
def trip_details(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    trip_details = {
        'location': trip.location,
        'people': trip.people,
        'money_required': trip.money_required,
        'description': trip.description
    }
    return jsonify(trip_details)

# Travel Route
@app.route('/travel', methods=['GET', 'POST'])
@login_required
def travel():
    # Initialize the form
    form = PlanYourTripForm()

    # Get the search query from the request if it exists
    search_query = request.args.get('search', '')

    # If there's a search query, filter trips based on location or username
    if search_query:
        trips = Trip.query.join(User).filter(
            (Trip.location.ilike(f"%{search_query}%")) |
            (User.username.ilike(f"%{search_query}%"))
        ).all()
    else:
        # If no search query, display all trips
        trips = Trip.query.join(User).all()

    # Handle form submission
    if form.validate_on_submit():
        new_trip = Trip(
            location=form.location.data,
            people=form.people.data,
            money_required=form.money_required.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(new_trip)
        db.session.commit()
        flash('Trip has been planned successfully!', 'success')
        return redirect(url_for('travel'))

    # Render the travel.html template with the trips and search form
    return render_template('travel.html', form=form, trips=trips)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
