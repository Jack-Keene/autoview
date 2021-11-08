from datetime import datetime, timedelta
from operator import inv 
from os import error
from flask import Flask, render_template, request, flash, session
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from sqlalchemy.sql import func
from werkzeug.utils import redirect
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField, DateTimeField, DecimalField, TimeField
from wtforms.validators import InputRequired, ValidationError
from functools import wraps
import requests
from wtforms.fields.core import DateField
from datetime import date, time
import os

app = Flask(__name__)

ENV = 'prod'
# Configure SQL Alchemy
if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:m4rt9r6H@localhost/autoviews'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sadvisqnhgpsei:f592e14d8a0953a894200076a9f7d646d5a7f04cd5b5c315c287515494cdb6cc@ec2-34-226-18-183.compute-1.amazonaws.com:5432/d7dl0398o6ip5r'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key="secret_key"

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

db= SQLAlchemy(app)

# Define database tables and data objects for Autoviews Database

class Users(db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    first_name = db.Column(db.String(length=100), nullable=False)
    last_name = db.Column(db.String(length=100), nullable=False)
    # email_address = db.Column(db.String(length=100), unique=True, nullable=False)
    username = db.Column(db.String(length=100), unique=True, nullable=False)
    hashed = db.Column(db.String(length=255), nullable=False)
    # postcode = db.Column(db.String(length=20), nullable=False)
    # street = db.Column(db.String(length=100), nullable=False)
    # number = db.Column(db.String(length=100), nullable=False)
    # phone_number = db.Column(db.String(length=20), nullable=False)
    type = db.Column(db.String(length=100), nullable=False)
    dealer_code = db.Column(db.Integer, db.ForeignKey('dealer.dealer_code'), nullable=True)
    # postcode = db.Column(db.String(length=20), nullable=False)
    # vehicles = db.relationship('Vehicles', backref='users', lazy=True)
    # booking = db.relationship('Bookings', backref='users', lazy=True)


    def __init__(self, first_name, last_name, username, hashed, type, dealer_code):
        self.first_name = first_name
        self.last_name = last_name
        # self.email_address = email_address
        self.username = username
        self.hashed = hashed
        # self.postcode = postcode
        # self.street = street
        # self.number = number
        # self.phone_number = phone_number
        self.type = type
        self.dealer_code = dealer_code
        
class Dealers(db.Model):
    __tablename__='dealer'
    dealer_code = db.Column(db.Integer, primary_key=True, nullable=False)
    dealer_name = street = db.Column(db.String(length=255), nullable=False)
    zone = db.Column(db.String(length=20), nullable=False)
    region = db.Column(db.String(length=20), nullable=False)
    postcode = db.Column(db.String(length=20), nullable=False)
    street = db.Column(db.String(length=100), nullable=False)
    number = db.Column(db.String(length=100), nullable=False)
    open_time = db.Column(db.Time(), nullable=False)
    close_time = db.Column(db.Time(), nullable=False)
    labour_cost = db.Column(db.Float, nullable=False)
    users = db.relationship('Users', backref='dealer', lazy=True)
    ramps = db.relationship('Ramp', backref='dealer', lazy=True)
    invoice = db.relationship('Invoice', backref='dealer', lazy=True)

    def __init__(self, dealer_name, zone, region, postcode, street, number, open_time, close_time, labour_cost):
        self.dealer_name = dealer_name
        self.zone = zone
        self.region = region
        self.postcode = postcode
        self.street = street
        self.number = number
        self.open_time = open_time
        self.close_time = close_time
        self.labour_cost = labour_cost

class Vehicles(db.Model):
    __tablename__='vehicles'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    registration = db.Column(db.String(length=100))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)
    make = db.Column(db.String(length=255), nullable=False)
    model = db.Column(db.String(length=255), nullable=False)
    year = db.Column(db.String(length=4), nullable=False)
    mot_date = db.Column(db.Date())
    booking = db.relationship('Booking', backref='vehicles', cascade="all, delete", lazy=True)

    def __init__(self, registration, owner_id, make, model, year, mot_date):
        self.registration = registration
        self.owner_id = owner_id
        self.make = make
        self.model = model
        self.year = year
        self.mot_date = mot_date

class Ramp(db.Model):
    __tablename__='ramps'
    ramp_id = db.Column(db.Integer, primary_key=True)
    dealer_code = db.Column(db.Integer, db.ForeignKey('dealer.dealer_code'), nullable=False)
    booking = db.relationship('Booking', backref='ramps', cascade='all, delete', lazy=True)
    availability = db.relationship('Availability', cascade='all, delete', backref='ramps', lazy=True)

    def __init__(self, dealer_code):
        self.dealer_code = dealer_code

class Booking(db.Model):
    __tablename__='booking'
    job_id = db.Column(db.Integer, primary_key=True)
    ramp_id = db.Column(db.Integer, db.ForeignKey('ramps.ramp_id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    start_time = db.Column(db.Time(), nullable=False)
    end_time = db.Column(db.Time(), nullable=False)
    day = db.Column(db.Date(), nullable=False)
    paid = db.Column(db.Boolean, nullable=False)
    availability = db.relationship('Availability', backref='booking', lazy=True)
    invoice = db.relationship('Invoice', backref='booking', cascade = 'delete, all', lazy=True)
    customer_quality = db.relationship('CustomerQuality', backref='booking', lazy=True)

    def __init__(self, ramp_id, owner_id, vehicle_id, start_time, end_time, day, paid):
        self.ramp_id = ramp_id
        self.owner_id = owner_id
        self.vehicle_id = vehicle_id
        self.start_time = start_time
        self.end_time = end_time
        self.day = day
        self.paid = paid
    
class Availability(db.Model):
    __tablename__='availability'
    slot_id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('booking.job_id'), nullable=True)
    ramp_id = db.Column(db.Integer, db.ForeignKey('ramps.ramp_id'), nullable=False)
    availability = db.Column(db.Boolean, nullable=False)
    start_time = db.Column(db.Time(), nullable=False)
    end_time = db.Column(db.Time(), nullable=False)
    day = db.Column(db.Date(), nullable=False)

    def __init__(self, job_id, ramp_id, availability, start_time, end_time, day):
        self.job_id = job_id
        self.ramp_id = ramp_id
        self.availability = availability
        self.start_time = start_time
        self.end_time = end_time
        self.day = day

def create_availability():
    dealers=db.session.query(Dealers).all()
    for day in range(30):
        print(day)
        for dealer in dealers:
            ramps = db.session.query(Ramp).filter(Ramp.dealer_code==dealer.dealer_code)
            for ramp in ramps:
                for hour in range(23):
                    data = Availability(job_id=None, ramp_id = ramp.ramp_id, availability = True, start_time = time(hour, 0), end_time= time(hour+1, 0), day = (date.today() + timedelta(days = 1) + timedelta(days = day)))
                    db.session.add(data)
                    db.session.commit()

class Invoice(db.Model):
    __tablename__='invoice'
    invoice_id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('booking.job_id'), nullable=False)
    dealer_code = db.Column(db.Integer, db.ForeignKey('dealer.dealer_code'), nullable=False)
    invoice_type = db.Column(db.String(length=255), nullable=False)
    part_number = db.Column(db.String(length=255))
    invoice_value= db.Column(db.Float(), nullable=False)
    invoice_date = db.Column(db.DateTime(timezone=False), default=func.now())

    def __init__(self, job_id, dealer_code, invoice_type, part_number, invoice_value):
        self.job_id = job_id
        self.dealer_code = dealer_code
        self.invoice_type = invoice_type
        self.part_number = part_number
        self.invoice_value = invoice_value

class CustomerQuality(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('booking.job_id'), nullable=False)
    overall = db.Column(db.Integer)
    speed = db.Column(db.Integer)
    quality = db.Column(db.Integer)
    comments = db.Column(db.Text)
    submit_date = db.Column(db.DateTime(timezone=False), default=func.now())
    completed = db.Column(db.Boolean)

    def __init__(self, job_id, overall, speed, quality, completed, comments):
        self.job_id = job_id
        self.overall = overall
        self.speed = speed
        self.quality = quality
        self.completed = completed
        self.comments = comments

@app.route('/chart')
def chart():
    data = db.session.query(Invoice).add_columns(Invoice.invoice_date, func.sum(Invoice.invoice_value)).group_by(Invoice.invoice_date, Invoice.invoice_id).all()
    
    labels = [str(datetime.strftime(row[1].date(), '%d:%m:%Y')) for row in data]
    values = [float(row[2]) for row in data]

    print(labels)
    print(values)
    return render_template('chart.html', values=values, labels=labels)
 
@app.route('/')
def index():
    if 'logged_in' in session.keys() and session['logged_in'] and session['access_level'] == 2:
        dashboard_data = {}
        user =  db.session.query(Users).filter(Users.id == session['id']).first()
        dealer_code = user.dealer_code
        today = datetime.today().date()
        week = (date.today() + timedelta(days = 7))
        # bookings = db.session.query(Booking).join(Ramp, Booking.ramp_id == Ramp.ramp_id).filter(Ramp.dealer_code == dealer_code).count()
        
        dashboard_data['bookings'] = db.session.query(Booking).join(Ramp, Booking.ramp_id == Ramp.ramp_id).filter(Ramp.dealer_code == dealer_code).count()
        dashboard_data['invoices'] = db.session.query(Booking).join(Ramp, Booking.ramp_id == Ramp.ramp_id).filter(Ramp.dealer_code == dealer_code, Booking.paid == False).count()
        data = db.session.query(Invoice).add_columns(Invoice.invoice_date, func.sum(Invoice.invoice_value)).group_by(Invoice.invoice_date, Invoice.invoice_id).all()

        times = db.session.query(Dealers).filter(Dealers.dealer_code == dealer_code).add_columns(Dealers.open_time, Dealers.close_time).first()
        open_hours = times.close_time.hour-times.open_time.hour
        ramps = db.session.query(Ramp).filter(Ramp.dealer_code == dealer_code).count()

        booking = db.session.query(Booking).join(Ramp, Booking.ramp_id == Ramp.ramp_id).filter(Booking.day > today, Booking.day <= week, Ramp.dealer_code == dealer_code).count()
        total_hours = ramps * open_hours * 7
        dashboard_data['efficiency'] = round(100*booking/total_hours,2)

        # print(efficiency)

        labels = [str(datetime.strftime(row[1].date(), '%d:%m:%Y')) for row in data]
        values = [float(row[2]) for row in data]
        print(dashboard_data)
        return render_template('home.html', values=values, labels=labels, dashboard_data=dashboard_data)
    else:
        return render_template('home.html')

class RegisterForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])
    # email_address = StringField('Email', [validators.Length(min=1, max=100)])
    username = StringField('Username', [validators.Length(min=4, max=100)])
    hashed = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    # street = StringField('Street Name', [validators.Length(min=1, max=100)])
    # number = StringField('House Number/Name', [validators.Length(min=1, max=100)])
    # phone_number = StringField('Phone Number', [validators.Length(min=1, max=20)])
    type = SelectField(u'Account Type', choices=[('Customer','Customer'), ('Dealer', 'Dealer'), ('Manufacturer', 'Manufacturer')])
    # postcode = StringField('Postcode', [validators.Length(min=1, max=50)])

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    # print(form.validate())
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        # email_address = form.email_address.data
        username = form.username.data
        hashed = sha256_crypt.hash(str(form.hashed.data))
        # street = form.street.data
        # number = form.number.data
        # phone_number = form.phone_number.data
        type = form.type.data
        # postcode = form.postcode.data
        result = db.session.query(Users).filter(Users.username==username).all()
        # email_check = db.session.query(Users).filter(Users.email_address==email_address).all()

        # Check both email and username do not exist
        if result == []:
            data = Users(first_name, last_name, username, hashed, type, None)
            db.session.add(data)
            db.session.commit()
            flash('You are now registered', 'success')
            return redirect('/login')
        else:
            flash('Username already exists', 'danger')
            return redirect('/register')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():

    ACCESS = {'guest': 0,
            'Customer': 1,
            'Dealer': 2,
            'Manufacturer': 3
            }

    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        # test to see if user exists
        result = db.session.query(Users).filter(Users.username==username).first()
        if result != None:
            password = result.hashed

            if sha256_crypt.verify(password_candidate, password):
                #login successful
                session['logged_in'] = True
                session['first_name'] = result.first_name
                session['id'] = result.id
                session['type'] = result.type
                session['access_level'] = ACCESS[result.type]
                session['dealer_code'] = result.dealer_code
                flash('You have successfully logged in', 'success')
                return redirect('/')
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

def login_required(access=0):
    def wrapper(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'access_level' not in session.keys():
                return redirect('/')
            if session['access_level'] >= access:
                return f(*args, **kwargs)
            else:
                return redirect('/')
        return wrap
    return wrapper

@app.route('/logout')
@login_required()
def logout():
    session.clear()
    return redirect('/')

@app.route('/booking', methods = ['GET', 'POST'])
@login_required(1)
def booking():
    time = 'Upcoming'
    if request.method=='POST':
        time =  request.form['type'] 

    today = date.today()
    if time == 'Upcoming':
        bookings = db.session.query(Booking).join(Ramp, Booking.ramp_id==Ramp.ramp_id).outerjoin(Invoice, Booking.job_id == Invoice.job_id).join(Dealers, Ramp.dealer_code==Dealers.dealer_code).join(Vehicles, Booking.vehicle_id==Vehicles.id).outerjoin(CustomerQuality, Booking.job_id == CustomerQuality.job_id).filter(Booking.owner_id == session['id'], Booking.day >= today).add_columns(Invoice.invoice_value, Booking.job_id, Booking.day, Booking.paid, Booking.start_time, Booking.end_time, Dealers.dealer_name, Vehicles.registration, Vehicles.make, Vehicles.model, CustomerQuality.completed).order_by(Booking.day, Booking.start_time ).all()
        print(bookings)
    elif time =='Past Bookings':
        bookings = db.session.query(Booking).join(Ramp, Booking.ramp_id==Ramp.ramp_id).outerjoin(Invoice, Booking.job_id == Invoice.job_id).join(Dealers, Ramp.dealer_code==Dealers.dealer_code).join(Vehicles, Booking.vehicle_id==Vehicles.id).outerjoin(CustomerQuality, Booking.job_id == CustomerQuality.job_id).filter(Booking.owner_id == session['id'], Booking.day < today).add_columns(Invoice.invoice_value, Booking.job_id, Booking.day, Booking.paid, Booking.start_time, Booking.end_time, Dealers.dealer_name, Vehicles.registration, Vehicles.make, Vehicles.model, CustomerQuality.completed).order_by(Booking.day,Booking.start_time).all()
    return render_template('booking.html', bookings=bookings, time=time)

def my_date_check(form, field):
    if field.data < datetime.now().date():
        raise ValidationError('got here')

class BookingForm(Form):
    registration = SelectField(u'Vehicle')
    dealer = SelectField(u'Dealer', coerce=str)
    day = DateField('Date', [validators.InputRequired() , my_date_check])

@app.route('/check_availability', methods = ['GET', 'POST'])
@login_required(1)
def check_availability():
    user = db.session.query(Vehicles).filter(Vehicles.owner_id == session['id']).add_columns(Vehicles.registration)
    dealer = db.session.query(Dealers).add_columns(Dealers.dealer_code, Dealers.dealer_name)

    form = BookingForm(request.form, obj=user)
    form.registration.choices = [(u.registration, u.registration) for u in user]
    form.dealer.choices = [(str(d.dealer_code) +" | " + d.dealer_name, str(d.dealer_code) +" | " + d.dealer_name) for d in dealer]

    if request.method == 'POST':
        if not form.validate():
            print(form.errors)
            error = 'Date must be in the future'
            return render_template('new_booking.html', error=error, form=form)
        else:
            return redirect(url_for('new_booking', day = form.day.data, dealer=form.dealer.raw_data[0].split(' | ')[0], registration = form.registration.data, **request.args))
            # return render_template('new_booking.html', day = form.day.data, dealer=form.dealer.data, registration = form.registration.data, **request.args)
    return render_template('new_booking.html', form=form)

@app.route('/new_booking', methods = ['POST', 'GET'])
@login_required(1)
def new_booking():
    day = request.args['day']
    dealer = request.args['dealer']
    registration = request.args['registration']
    
    availability = db.session.query(Availability).join(Ramp, Availability.ramp_id == Ramp.ramp_id).join(Dealers, Ramp.dealer_code == Dealers.dealer_code).filter(Availability.day == day, Availability.availability == True, Availability.start_time > Dealers.open_time, Availability.end_time< Dealers.close_time, Dealers.dealer_code== dealer).add_columns(Availability.day, Availability.start_time, Dealers.dealer_code).distinct(Availability.start_time).all()
    if request.method == 'POST':
        submit_time = datetime.strptime(request.form['time'], '%H:%M:%S').time()
        hour = submit_time.hour
        end_time =  time(hour+1, 0)
        ramps = db.session.query(Availability).join(Ramp, Availability.ramp_id == Ramp.ramp_id).join(Dealers, Ramp.dealer_code == Dealers.dealer_code).filter(Availability.day == day, Availability.availability == True, Availability.start_time == submit_time, Dealers.dealer_code== dealer).add_columns(Ramp.ramp_id).first()
        vehicle_id = db.session.query(Vehicles).filter(Vehicles.registration ==  registration).add_columns(Vehicles.id).first()
        booking = Booking(ramps.ramp_id, session['id'], vehicle_id.id, submit_time, end_time, day, False)
        db.session.add(booking)
        db.session.commit()
        job = db.session.query(Booking).filter(Booking.ramp_id ==  ramps.ramp_id, Booking.start_time == submit_time, Booking.day == day).first()
        job_id = job.job_id
        Availability.query.filter(Availability.ramp_id==ramps.ramp_id, Availability.day==day, Availability.start_time==submit_time).update(dict(availability=False, job_id=job_id))
        db.session.add(booking)
        db.session.commit()

        flash('Booking successful', 'success')
        return redirect('/booking')

    return render_template('submit_booking.html', availability=availability, registration=registration, day=day, dealer=dealer)

@app.route('/cancel_booking/<string:id>', methods=['POST'])
@login_required(1)
def cancel_booking(id):
    if request.method == 'POST':
        result = Booking.query.filter(Booking.job_id == id).first()
        db.session.delete(result)
        db.session.commit()
        flash('Booking cancelled', 'success')
    return redirect('/booking')

@app.route('/vehicle', methods = ['GET'])
@login_required(1)
def vehicle():
    vehicles = db.session.query(Vehicles).filter(Vehicles.owner_id==session['id']).all()
    return render_template('vehicle.html', vehicles=vehicles)

def vehicle_lookup(registration):
    # Use DVLA API to lookup vehicle information and history

    url = "https://driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles"
    payload = "{\n\t\"registrationNumber\": \"" + registration + "\"\n}"

    headers = {
            'x-api-key': 'XmIieBuFvltjahQmOzrc665g39ePuF467hDAt6j7',
            'Content-Type': 'application/json'
                }

    response = requests.request("POST", url, headers=headers, data = payload)
    vehicle_details = response.json()

    # if 'motExpiryDate' not in vehicle_details.keys():
    #     years = 365*3
    #     expiry = datetime.strptime(vehicle_details['monthOfFirstRegistration'], '%Y-%m').date() + timedelta(days = years)
    #     vehicle_details['motExpiryDate'] = expiry

    if 'errors' in vehicle_details:
        return None
    elif 'motExpiryDate' not in vehicle_details.keys():
        years = 365*3
        expiry = datetime.strptime(vehicle_details['monthOfFirstRegistration'], '%Y-%m').date() + timedelta(days = years)
        vehicle_details['motExpiryDate'] = expiry
    else:
        return {
            "make": vehicle_details['make'],
            "model": vehicle_details['colour'],
            "year": vehicle_details['yearOfManufacture'],
            "mot_date": vehicle_details['motExpiryDate']
        }    

@app.route('/add_vehicle', methods = ['GET', 'POST'])
@login_required(1)
def add_vehicle():
    if request.method == 'POST':
        registration = request.form['registration']

        # search dvla API for inputted vehicle
        vehicle_detail = vehicle_lookup(registration)
        if vehicle_detail != None:
            data = Vehicles(registration.upper(), session['id'], vehicle_detail['make'].lower(), vehicle_detail['model'].lower(), vehicle_detail['year'], vehicle_detail['mot_date'])
            db.session.add(data)
            db.session.commit()
            flash('Vehicle added successfully', 'success')
            return redirect('/vehicle')
        else:
            error = 'Vehicle not found'
            return render_template('add_vehicle.html', error=error)
    return render_template('add_vehicle.html')

@app.route('/delete_vehicle/<string:id>', methods = ['POST'])
@login_required(1)
def delete_vehicle(id):
    if request.method == 'POST':
        result = Vehicles.query.filter(Vehicles.id==id, Vehicles.owner_id==session['id']).first()
        db.session.delete(result)
        db.session.commit()
        flash('Vehicle Deleted', 'success')
    return redirect('/vehicle')

class Dealer(Form):
    dealer_name = StringField('Dealer Name', [validators.Length(min=1, max=255)])
    zone = SelectField(u'Zone', choices=[('N1','N1'), ('N2', 'N2'), ('S1', 'S1'), ('S2', 'S2')])
    region = SelectField(u'Region', choices=[('North','North'), ('South', 'South')])
    postcode = StringField('Dealer Name', [validators.Length(min=1, max=255)])
    street = StringField('Dealer Name', [validators.Length(min=1, max=255)])
    number = StringField('Dealer Name', [validators.Length(min=1, max=255)])
    open_time = TimeField('Open Time', format='%H:%M')
    close_time = TimeField('Close Time', format='%H:%M')
    labour_cost = DecimalField('Labour Cost')

@app.route('/dealer')
@login_required(3)
def dealer():
    dealers = db.session.query(Dealers).all()
    return render_template('dealer.html', dealers=dealers)

@app.route('/add_dealer', methods=['POST', 'GET'])
@login_required(3)
def new_dealer():
    form = Dealer(request.form)
    if request.method == 'POST':
        dealer_name = form.dealer_name.data
        zone = form.zone.data
        region = form.region.data
        postcode = form.postcode.data
        street = form.street.data
        number = form.number.data
        open_time = form.open_time.data
        close_time = form.close_time.data
        labour_cost = float(form.labour_cost.data)

        data = Dealers(dealer_name, zone, region, postcode, street, number, open_time, close_time, labour_cost)
        db.session.add(data)
        db.session.commit()
        flash('New Dealer Added', 'success')
        return redirect('/dealer')

    return render_template('add_dealer.html', form=form)

@app.route('/delete_dealer/<string:id>', methods = ['POST'])
@login_required(3)
def delete_dealer(id):
    if request.method == 'POST':
        result = Dealers.query.filter_by(dealer_code=id).first()
        db.session.delete(result)
        db.session.commit()
        flash('Dealer Terminated', 'success')
    return redirect('/dealer')
    
@app.route('/ramps', methods=['GET'])
@login_required(2)
def ramps():
    user =  db.session.query(Users).filter(Users.id == session['id']).first()
    dealer_code = user.dealer_code
    if dealer_code != None:
        ramps = Ramp.query.join(Dealers, Ramp.dealer_code==Dealers.dealer_code).add_columns(Ramp.ramp_id, Dealers.dealer_code, Dealers.dealer_name, Dealers.open_time, Dealers.close_time).filter(Ramp.dealer_code==dealer_code).all()
        return render_template('ramps.html', ramps=ramps)
    else:
        error = 'No Ramps Found'
        return render_template('ramps.html', error=error)

@app.route('/add_ramp', methods=['POST'])
@login_required(2)
def add_ramp():
    if request.method == 'POST':
        user =  db.session.query(Users).filter(Users.id == session['id']).first()
        dealer_code = user.dealer_code
        if dealer_code != None:
            data = Ramp(dealer_code)
            db.session.add(data)
            db.session.commit()
            flash('Ramp Added', 'success')
            return redirect('/ramps')
        else:
            error = 'No dealer selected'
            return render_template('ramps.html', error=error)

@app.route('/delete_ramp/<string:id>', methods = ['POST'])
@login_required(2)
def delete_ramp(id):
    if request.method == 'POST':
        result = Ramp.query.filter_by(ramp_id=id).first()
        db.session.delete(result)
        db.session.commit()
        flash('Ramp deleted', 'success')
    return redirect('/ramps')

@app.route('/dealer_bookings', methods=['POST', 'GET'])
@login_required(2)
def dealer_booking():
    user =  db.session.query(Users).filter(Users.id == session['id']).first()
    dealer_code = user.dealer_code
    paid = False
    status = {'Unpaid':False, 'Paid':True}
    header = 'Unpaid'
    # today = datetime.today().date()
    if request.method == 'POST':
        paid = status[request.form['type']]
        header = request.form['type']

    bookings = db.session.query(Booking).join(Ramp, Booking.ramp_id==Ramp.ramp_id).join(Dealers, Dealers.dealer_code==Ramp.dealer_code).join(Users, Booking.owner_id==Users.id).join(Vehicles, Booking.vehicle_id==Vehicles.id).filter(Booking.paid == paid, Dealers.dealer_code == dealer_code).add_columns(Booking.job_id, Booking.ramp_id, Booking.day, Booking.start_time, Users.first_name, Users.last_name, Vehicles.make, Vehicles.registration, Booking.owner_id).all()
    return render_template('dealer_bookings.html', bookings=bookings, status=header)

@app.route('/dealer_information', methods=['POST', 'GET'])
@login_required(2)
def my_dealer():
    user =  db.session.query(Users).filter(Users.id == session['id']).first()
    dealer_code = user.dealer_code
    dealer_info = db.session.query(Dealers).filter(Dealers.dealer_code == dealer_code).first()
    if request.method == 'POST':
        db.session.query(Dealers).filter(Dealers.dealer_code==dealer_code).update(dict(open_time=request.form['open_time'], close_time=request.form['close_time'], labour_cost=request.form['labour_cost']))
        db.session.commit()
        flash('Details Updated', 'success')
        return redirect('/dealer_information')
    return render_template("dealer_information.html", dealer_info=dealer_info)

@app.route('/view_customer/<string:id>', methods=['POST'])
@login_required(2)
def view_customer(id):
    stats = {}
    if request.method == 'POST':
        customer = db.session.query(Users).filter(Users.id == id).first()
        visits = db.session.query(Booking).join(Invoice, Booking.job_id==Invoice.job_id).filter(Booking.owner_id == id, Invoice.dealer_code == session['dealer_code']).add_columns(Booking.job_id, Invoice.invoice_value, Invoice.invoice_date).all()
        stats['visits'] = len(visits)
        stats['spend'] = round(sum([row[2] for row in visits]))
        stats['elapsed'] = (datetime.today().date() - max([row[3] for row in visits]).date()).days
        stats['customer'] = customer
        stats['vehicles'] = db.session.query(Vehicles).filter(Vehicles.owner_id==id).all()
        stats['average_spend'] = round(stats['spend']/stats['visits'])
        return render_template('view_customer.html', stats=stats)

@app.route('/invoice/<string:id>', methods=['GET', 'POST'])
@login_required(2)
def invoice(id):
    invoice = db.session.query(Invoice).join(Booking, Invoice.job_id==Booking.job_id).filter(Invoice.job_id==id).add_columns(Booking.owner_id,Booking.job_id, Invoice.invoice_type, Invoice.invoice_value, Invoice.invoice_date).all()
    if invoice == []:
        if request.method == 'POST' and request.form['_method']=='RAISE':
            user =  db.session.query(Users).join(Dealers, Users.dealer_code==Dealers.dealer_code).filter(Users.id == session['id']).add_columns(Dealers.labour_cost, Dealers.dealer_code).first()
            labour = float(request.form['hours']) * user.labour_cost
            data = Invoice(id, user.dealer_code, 'Labour', None, labour)
            db.session.add(data)
            db.session.commit()
            flash('Invoice Submitted', 'success')
            return redirect('/dealer_bookings')
        else:
            return render_template('raise_invoice.html')
    else:
        return render_template('invoice.html', invoice=invoice)

@app.route('/customer_invoices', methods=['GET', 'POST'])
@login_required(1)
def customer_invoices():
    
    dict_ = {'Paid':True, 'Unpaid':False}
    time = False
    if request.method=='POST':
        time =  dict_[request.form['type']] 

    invoices = db.session.query(Booking).join(Invoice, Booking.job_id == Invoice.job_id).join(Ramp, Booking.ramp_id==Ramp.ramp_id).join(Dealers, Ramp.dealer_code==Dealers.dealer_code).join(Vehicles, Booking.vehicle_id==Vehicles.id).outerjoin(CustomerQuality, Booking.job_id == CustomerQuality.job_id).filter(Booking.owner_id == session['id'], Booking.paid == time).add_columns(Booking.job_id, CustomerQuality.completed ,Booking.day, Booking.start_time, Dealers.dealer_name, Vehicles.registration, Vehicles.make, Vehicles.model, Invoice.invoice_value, Booking.paid).order_by(CustomerQuality.completed.desc(), Booking.day.desc()).all()
    return render_template('customer_invoices.html', invoices=invoices)

@app.route('/pay_invoice/<string:id>', methods=['GET','POST'])
@login_required(1)
def pay_invoice(id):
    invoice =  db.session.query(Invoice).join(Booking, Invoice.job_id==Booking.job_id).outerjoin(CustomerQuality, Invoice.job_id==CustomerQuality.job_id).filter(Invoice.job_id==id).add_columns(Booking.owner_id,Booking.job_id, Booking.paid, Invoice.invoice_type, Invoice.invoice_value, Invoice.invoice_date, CustomerQuality.completed).first()
    print(invoice)
    if invoice != None and not invoice.paid:
        if request.method == 'POST' and request.form['_method']=='PAY':
            print('got here')
            booking = db.session.query(Booking).filter(Booking.job_id==id).first()
            booking.paid = True
            db.session.commit()
            return redirect ('/customer_invoices')
        return render_template('pay_invoice.html', booking=invoice)
    return render_template('customer_invoice.html', invoice=invoice)

@app.route('/customer_feedback/<string:id>', methods=['GET','POST'])
@login_required(1)
def customer_feedback(id):
    print(list(request.form.keys()))
    if request.method =='POST' and ['speed','quality','overall','comments'] == list(request.form.keys()):
        data = CustomerQuality(id, request.form['overall'], request.form['speed'], request.form['quality'], True, request.form['comments'])
        print(request.form['comments'])
        db.session.add(data)
        db.session.commit()
        flash('Thank you for your feedback', 'success')
        return redirect('/booking')
    elif request.method =='POST': 
        error = 'Please fill in all sections'
        return render_template('customer_feedback.html', error=error)

    return render_template('customer_feedback.html')

@app.route('/view_feedback', methods=['POST', 'GET'])
@login_required(2)
def view_feedback():
    user =  db.session.query(Users).filter(Users.id == session['id']).first()
    dealer_code = user.dealer_code
    all_feedback = db.session.query(CustomerQuality).join(Invoice, CustomerQuality.job_id == Invoice.job_id).join(Booking, CustomerQuality.job_id==Booking.job_id).join(Users, Booking.owner_id==Users.id).filter(Invoice.dealer_code == dealer_code).add_columns(Users.first_name, Booking.day, Users.last_name, CustomerQuality.comments, CustomerQuality.overall, CustomerQuality.quality, CustomerQuality.speed).all()
    feedback = db.session.query(func.count(CustomerQuality.overall)).join(Invoice, CustomerQuality.job_id == Invoice.job_id).filter(Invoice.dealer_code == dealer_code).group_by(CustomerQuality.overall).add_columns(CustomerQuality.overall).order_by(CustomerQuality.overall.desc()).all()
    labels = [5,4,3,2,1]
    data = [row[0] for row in feedback]
    count= sum([row[0] for row in feedback])
    if count != 0:
        average = round(sum([row[1] * row[0] for row in feedback])/count,2)
    else:
        average=0
    stats = {'average':average,
            'count':count}

    return render_template('view_feedback.html', data=data, labels=labels, stats=stats, all_feedback=all_feedback)

@app.route('/set_dealer', methods= ['POST', 'GET'])
@login_required(2)
def set_dealer():
    dealers = db.session.query(Dealers).add_columns(Dealers.dealer_code, Dealers.dealer_name).all()
    if request.method == 'POST':
        dealer = request.form['registration'].split('| ')[1]
        session['dealer_code'] = dealer
        db.session.query(Users).filter(Users.id==session['id']).update(dict(dealer_code=dealer))
        db.session.commit()
        flash('Details Updated', 'success')

    return render_template('set_dealer.html', dealers=dealers)

if __name__ == "__main__":
    # create_availability()
    app.run() 
