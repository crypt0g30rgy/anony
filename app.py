from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import Swagger
from dotenv import load_dotenv
import os
import uuid
from validate_email_address import validate_email


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv(
    'SECRET_KEY')  # Set a secret key for security

mail = Mail(app)
db = SQLAlchemy(app)
swagger = Swagger(app)

# Flask-Security setup using the User and Role classes
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary='user_roles')


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class UserRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


class Feedback(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(120))
    submitted = db.Column(db.Boolean, default=False)  # Added boolean flag


class UserFeedback(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    feedback = db.Column(db.Text, nullable=False)


def is_valid_uuid(uuid_str):
    try:
        uuid.UUID(uuid_str, version=4)
        return True
    except ValueError:
        return False


@app.route('/')
def index():
    """
    Home endpoint.
    ---
    responses:
      200:
        description: Returns the welcome message
    """
    return render_template('index.html')


@app.route('/api/hello', methods=['GET'])
def hello():
    """
    Hello World API.
    ---
    responses:
      200:
        description: Returns the hello message
    """
    return jsonify(message="Hello, World!")

# Admin Page


@app.route('/admin')
# @login_required
def admin():
    """
    Admin Page.
    ---
    responses:
      200:
        description: Renders the admin page.
    """
    return render_template('admin.html')


@app.route('/api/all_feedbacks', methods=['GET'])
# @login_required
def get_all_feedbacks():
    """
    Fetch All Feedbacks API.
    ---
    responses:
      200:
        description: Returns a list of all feedback entries
    """
    # Check if the user has permission to access this endpoint (optional)
    # if not user_has_permission(current_user):
    #     return jsonify(message="You do not have permission to access this endpoint."), 403

    # Fetch all feedback entries from the database
    all_feedbacks = UserFeedback.query.all()

    # Convert feedback entries to a list of dictionaries
    feedback_list = [
        {
            'id': feedback.id,
            'email': feedback.email,
            'feedback': feedback.feedback,
        }
        for feedback in all_feedbacks
    ]

    return jsonify(feedbacks=feedback_list)


@app.route('/api/send_invite', methods=['POST'])
# @login_required  # Protect the endpoint with login requirement
def send_invite():
    """
    Send Invite API.
    ---
    parameters:
      - name: emails
        in: body
        type: array
        items:
          type: string
        required: true
        description: Array of email addresses to send the invite.
    responses:
      200:
        description: Returns a success message
    """
    data = request.get_json()

    if 'emails' not in data:
        return jsonify(message="No 'emails' key found in the JSON payload."), 400

    emails = data['emails']

    if not emails or not all(isinstance(email, str) for email in emails):
        return jsonify(message="Invalid or empty email array."), 400

    success_messages = []
    error_messages = []

    base_url = os.getenv('BASE_URL')

    with app.app_context():
        for email in emails:
            # Check if the email is already in the database
            if Feedback.query.filter_by(email=email).first():
                error_messages.append(f"Email '{email}' already invited!")
                continue

            # Generate a unique ID for the feedback
            feedback_id = str(uuid.uuid4())

            # Save the feedback ID and email in the database
            feedback = Feedback(id=feedback_id, email=email)
            db.session.add(feedback)
            db.session.commit()

            # Send the email invite
            msg = Message('Feedback Invitation', recipients=[email])
            msg.body = f'Click the following link to provide anonymous feedback: {base_url}/feedback/{feedback_id}'

            try:
                mail.send(msg)
                success_messages.append(f"Invite sent successfully to {email}")
            except Exception as e:
                error_messages.append(
                    f"Error sending invite to {email}: {str(e)}")

    return jsonify(success=success_messages, error=error_messages)


@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    """
    Submit Feedback API.
    ---
    parameters:
      - name: data
        in: body
        type: object
        required: true
        description: JSON object containing UUID and feedback.
        schema:
          properties:
            uuid:
              type: string
            feedback:
              type: string
    responses:
      200:
        description: Returns a success message
    """
    data = request.get_json()

    if 'uuid' not in data or 'feedback' not in data:
        return jsonify(message="Invalid or missing 'uuid' or 'feedback' in the JSON payload."), 400

    uuid_value = data['uuid']
    feedback_text = data['feedback']

    # Validate UUID
    if not is_valid_uuid(uuid_value):
        return jsonify(message="Invalid UUID format."), 400

    # Check if the UUID exists in the database
    feedback_entry = Feedback.query.filter_by(id=uuid_value).first()

    if not feedback_entry:
        return jsonify(message=f"UUID '{uuid_value}' not found."), 404

    # Check if feedback has already been submitted
    if feedback_entry.submitted:
        return jsonify(message="Feedback already submitted for this UUID."), 400

    # Validate Email
    if not validate_email(feedback_entry.email):
        return jsonify(message="Invalid email address."), 400

    # Save feedback along with the associated email in the database
    user_feedback = UserFeedback(
        id=uuid_value, email=feedback_entry.email, feedback=feedback_text)
    db.session.add(user_feedback)

    # Update the submitted field for the feedback_entry
    feedback_entry.submitted = True
    db.session.commit()

    return jsonify(message="Feedback submitted successfully!")


@app.route('/feedback_form')
def feedback_form():
    """
    Feedback Form Page.
    ---
    responses:
      200:
        description: Renders the feedback form page.
    """
    uuid_value = request.args.get('uuid')

    if not uuid_value:
        return jsonify(message="UUID not found in the query parameters."), 400

    return render_template('feedback_form.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables before running the app
    app.run(debug=True)
