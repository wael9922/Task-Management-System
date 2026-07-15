from taskmanager.models import User, Task, Activity
from flask_mail import Message
from taskmanager import db, mail, app
from flask import url_for, render_template
from datetime import datetime
from flask_login import current_user
from sqlalchemy import or_, func
import os
from PIL import Image
import secrets
from email_validator import validate_email, EmailNotValidError


def send_reset_email(user: User):
    """Send password reset email to the user"""

    token = user.request_reset_token() # return a token and send it to the user email
    msg = Message(
        subject="Password Reset Request",
        sender=app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    full_token = url_for('users.reset_token', token=token, _external=True)
    msg.html = render_template(
        "email.html",
        reset_token=full_token
    )

    mail.send(msg)




def get_cards():
    """Get the data for the dashboard cards"""

    # Get the count of tasks created by the user
    created_tasks_count = db.session.scalar(
        db.select(func.count(Task.id))
        .where(Task.creator == current_user.id)
    )

    # Get the count of tasks assigned to the user
    assigned_tasks_count = db.session.scalar(
        db.select(func.count(Task.id))
        .where(Task.assignee == current_user.id)
    )

    # Get the count of pending tasks assigned to the user
    pending_tasks_count = db.session.scalar(
        db.select(func.count(Task.id))
        .where(
            Task.assignee == current_user.id,
            Task.status == "Pending"
        )
    )

    # Get the count of completed tasks assigned to the user or created by him
    completed_tasks_count = db.session.scalar(
        db.select(func.count(Task.id))
        .where(
            or_(
                Task.creator == current_user.id,
                Task.assignee == current_user.id
            ),
            Task.status == "Completed"
        )
    )

    cards = {
        "created": created_tasks_count,
        "assigned": assigned_tasks_count,
        "pending": pending_tasks_count,
        "completed": completed_tasks_count
    }
    return cards


def get_recent_activities():
    """
    Query the most recent activities for the user
    Return:
         recent_activities: list of structured activities
    """
    # Query the recent activities and organize them by type,
    activities = db.session.execute(
        db.select(
            Activity.type,
            Activity.task_id,
            Activity.actor_id,
            Activity.recipient_id,
            Activity.created_at
        ).where(
            or_(
            Activity.recipient_id == current_user.id,
            Activity.actor_id == current_user.id
            )
        ).order_by(
            Activity.created_at.desc()
        ).limit(5)
    ).all()
    print(len(activities))
    recent_activities = []
    for activity in activities:
        data = {}
        # Current user has a completed a task he created and assigned it to himself
        if (activity.type == "completion" and
            activity.actor_id == current_user.id and
                activity.recipient_id == current_user.id
            ):
            data = {
                "message" : "You completed a task.",
                "task_id": activity.task_id,
                "date": activity.created_at,
            }
            recent_activities.append(data)

        # Current user is the task creator but isn't the assignee, the assignee has completed the task
        # There is no need to check for recipient_id
        # If current user isn't the actor then he got this activity because he matched the recipient in the query already
        elif (activity.type == "completion" and
              activity.actor_id != current_user.id
             ):
            actor = User.query.get(activity.actor_id)
            data = {
                "message" : f"{actor.username} has completed the task you assigned him",
                "task_id": activity.task_id,
                "date": activity.created_at,
            }
            recent_activities.append(data)

        # Current user completed a task was assigned to him by other user
        elif (activity.type == "completion" and
              activity.actor_id == current_user.id and
              activity.recipient_id != current_user.id
             ):
            creator = User.query.get(activity.recipient_id)
            data = {
                "message" : f"You completed the task was assigned to you by {creator.username}",
                "task_id": activity.task_id,
                "date": activity.created_at,
            }
            recent_activities.append(data)

        # Current user get a task assignment from another user
        elif (activity.type == "assignment" and
              activity.recipient_id == current_user.id
            ):
            creator = User.query.get(activity.actor_id)
            data = {
                "message" : f"You have been assigned a task by {creator.username}",
                "task_id": activity.task_id,
                "date": activity.created_at,
            }
            recent_activities.append(data)
    recent_activities.sort(key=lambda x: x["date"], reverse=True)
    return recent_activities


def save_picture(form_picture):
    """
    Update image name and resize it

    Return:
        updated_image_filename: str
    """
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_picture.filename) # keep the extension and discard the name
    picture_filename = random_hex + file_extension # create a new unique name
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_filename)

    output_size = (125, 125)
    img = Image.open(form_picture)
    img.thumbnail(output_size) # Resizing
    img.save(picture_path)

    return picture_filename




def is_valid_email(email):
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


# Add argument validator and type casting
def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()







