from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms.fields import(
    SelectField,
    BooleanField,
    TextAreaField,
    DateField,
    EmailField,
    StringField,
    SubmitField,
    PasswordField
)
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from taskmanager.models import User
from datetime import date
from taskmanager import bcrypt


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=20)]
    )
    email = EmailField(
        "Email",
        validators=[DataRequired()]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=30)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("There is already account registered with this email address")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Username is taken, please pick another one")


class LoginForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[DataRequired()]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class TaskForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[DataRequired()]
    )
    details = TextAreaField(
        "Task Details",
        validators=[DataRequired()]
    )
    assigned_to = StringField(
        "Assigned To",
        description="Please leave blank if this task is your responsibility."
    )
    deadline = DateField(
        "Deadline",
        validators=[Optional()]
    )
    status = SelectField(
        "Status",
        choices=[
            ("Pending", "Pending"),
            ("In Progress", "In Progress"),
            ("Completed", "Completed")
        ]
    )

    submit = SubmitField("Create")

    # Check if the assignee user exists, if it doesn't raise an error
    def validate_assigned_to(self, assigned_to):
        if not assigned_to.data.strip() == "": # if assignee is blank or empty space then creator is the assignee
            user = User.query.filter_by(username=assigned_to.data).first()
            if user is None:
                raise ValidationError("This user doesn't exist")

    # Ensure deadline is not a past date
    def validate_deadline(self, deadline):
        if deadline.data is not None:
            if date.today() > deadline.data:
                raise ValidationError("Deadline must be in future date")


class RequestResetForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[DataRequired()]
    )
    submit = SubmitField("Send Reset Request")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("No account found with this email address")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=30)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")



class UpdateEmailForm(FlaskForm):
    email = EmailField(
        "New Email",
        validators=[DataRequired()]
    )
    confirm_email = EmailField(
        "Confirm New Email",
        validators=[DataRequired(), EqualTo("email")]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=30)]
    )
    submit = SubmitField("Update")

    def validate_email(self, email):
        if current_user.email == email.data: # If user enters his current email
            raise ValidationError("This is your current email address, You need to enter a new email address.")

        user = User.query.filter_by(email=email.data).first()

        if user is not None:
            raise ValidationError("There is already account registered with this email address")

    def validate_password(self, password):
        # Ensure that email can't be changed without a correct password
        if not bcrypt.check_password_hash(current_user.password, password.data):
            raise ValidationError("Incorrect Password")


# Update password, current password is I didn't use the Reset Password Form
class UpdatePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired()]
    )

    password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=8, max=30)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Update")

    def validate_current_password(self, current_password):
        # Ensure that password can't be changed without a correct current password
        if not bcrypt.check_password_hash(current_user.password, current_password.data):
            raise ValidationError("Incorrect current password")


# This is used to confirm actions
class EmptyForm(FlaskForm):
    submit = SubmitField()



class UpdateProfilePicForm(FlaskForm):
    image_file = FileField(
        "Update Profile Picture",
        validators=[FileAllowed(["jpg", "png", "jpeg"])]
    )

    submit = SubmitField("Save Picture")