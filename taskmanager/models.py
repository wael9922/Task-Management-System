from itsdangerous import URLSafeTimedSerializer as Serializer
from sqlalchemy import ForeignKey
from taskmanager import db, app, login_manager
from flask_login import UserMixin
from datetime import date


# Creating a login session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    image_file = db.Column(db.String(100), default="default.jpg")

    created_tasks  = db.relationship("Task", foreign_keys="Task.creator",  back_populates="task_creator")
    assigned_tasks = db.relationship("Task", foreign_keys="Task.assignee", back_populates="task_assignee", cascade="all, delete-orphan")

    def request_reset_token(self):
        s = Serializer(app.config["SECRET_KEY"])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token,  expires_sec=1800):
        s = Serializer(app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}')"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    details = db.Column(db.Text)

    creator = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assignee = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    deadline = db.Column(db.Date)
    status = db.Column(db.String(40), nullable=False)

    task_creator = db.relationship("User", foreign_keys=[creator], back_populates="created_tasks")
    task_assignee = db.relationship("User", foreign_keys=[assignee], back_populates="assigned_tasks")

    def __repr__(self):
        return f"Task('{self.id}', '{self.title}')"



class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String, nullable=False)
    recipient_id = db.Column(db.Integer, nullable=False)
    actor_id = db.Column(db.Integer)
    task_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.Date, default=date.today)

    def __repr__(self):
        return f"Activity('{self.id}', '{self.type}')"

