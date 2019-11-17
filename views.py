from configparser import ConfigParser
from flask import Flask, render_template, request, redirect, url_for
from flask_mongoengine import MongoEngine, Document
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, Length, InputRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

from data_downloader import download, get_patients, get_patient, get_patient_plans_ids

appConfig = ConfigParser()
appConfig.read("config.ini")

download()

app = Flask(__name__)

app.config['MONGODB_SETTINGS'] = {
    'db': appConfig.get("CoreContext", "mongo_db"),
    'host': appConfig.get("CoreContext", "mongo")
}

db = MongoEngine(app)
app.config['SECRET_KEY'] = appConfig.get("CoreContext", "secret_key")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Document):
    meta = {'collection': 'users'}
    email = db.StringField(max_length=30)
    password = db.StringField()

@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()

class RegForm(FlaskForm):
    first_name = StringField('first_name', render_kw={'class' : 'form-control form-control-user', 'placeholder':"First Name"})
    last_name = StringField('last_name', render_kw={'class' : 'form-control form-control-user', 'placeholder':"Last Name"})
    email = StringField('email', render_kw={'class' : 'form-control form-control-user', 'placeholder':"Email Address"}, validators=[InputRequired(), Email(message='Invalid email'), Length(max=30)])
    password = PasswordField('password', render_kw={'class' : 'form-control form-control-user', 'placeholder':"Password"}, validators=[InputRequired(), Length(min=2, max=20)])

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegForm()
    if request.method == 'POST':
        if form.validate():
            existing_user = User.objects(email=form.email.data).first()
            if existing_user is None:
                hashpass = generate_password_hash(form.password.data, method='sha256')
                hey = User(form.email.data,hashpass).save()
                login_user(hey)
                return redirect(url_for('tables'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegForm()
    if request.method == 'POST':
        if form.validate():
            check_user = User.objects(email=form.email.data).first()
            if check_user:
                if check_password_hash(check_user['password'], form.password.data):
                    login_user(check_user)
                    return redirect(url_for('tables'))
    return render_template('login.html', form=form)

@app.route('/dashboard/<id>')
@login_required
def dashboard(id):
    return render_template('index.html', patient=get_patient(id), plans=get_patient_plans_ids(id))

@app.route('/plan/<id>')
@login_required
def plan(id):
    return render_template('plan.html', tests=[{'Id': 10, 'Name': 'Test3', 'Details': 'OK'}], comments=[{'Author':'Pawel', 'Text': 'It is alright', 'Date': datetime.utcnow().date()}])

@app.route('/tables')
@login_required
def tables():
    return render_template('tables.html', patients=get_patients(), now=datetime.utcnow().date())

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('tables'))
    else:
        return redirect(url_for('login'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

@app.route('/logout', methods = ['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run()