# def create_notification(notify_type, recipient_id, actor_id, task_id):
#     notification = Notification(
#         type=notify_type,
#         recipient_id=recipient_id,
#         actor_id=actor_id,
#         task_id=task_id
#     )
#     db.session.add(notification)
#     db.session.commit()

# Email body
# msg.body = f"""To reset your password, visit the following link:
# {url_for('users.reset_token', token=token, _external=True)}
#
# If you did not make this request, simply ignore this email and no changes will be made.
# """


# def get_approaching_deadline():
#     due_tomorrow = date.today() + timedelta(days=1)
#     if datetime.now():
#         pass
#     stmt = db.select(
#         Task.id,
#         Task.title,
#         Task.deadline
#     ).where(
#         Task.assignee == current_user.id,
#         Task.status != "Completed",
#         Task.deadline == due_tomorrow
#     )
#     tasks = db.session.execute(stmt).all()

    # if tasks:
    #     for task in tasks:
    #         create_notification(
    #             notify_type="Deadline",
    #             recipient_id=current_user.id,
    #             actor_id=None,
    #             task_id=task.id
    #         )

import re

