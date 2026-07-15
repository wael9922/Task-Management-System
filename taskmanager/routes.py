from sqlalchemy import or_
from taskmanager import app, bcrypt, db
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)
from taskmanager.forms import(
    TaskForm, RegisterForm,
    LoginForm, EmptyForm,
    RequestResetForm, ResetPasswordForm,
    UpdateEmailForm, UpdatePasswordForm,
    UpdateProfilePicForm
)
from flask_login import current_user, login_required, login_user, logout_user
from taskmanager.models import User, Task, Activity
from datetime import date
from taskmanager.utils import send_reset_email, get_recent_activities, get_cards, save_picture


@app.route("/")
@app.route("/home")
@login_required
def home():
    page = request.args.get("page", 1, type=int)
    filter_by = request.args.get("filter_by", "all")
    status = request.args.get("by_status", "all")
    # Start with an empty query
    stmt = db.select(Task)

    # Filter by creator/assignee
    if filter_by == "created_by_me":
        stmt = stmt.where(
            Task.creator == current_user.id
        )

    elif filter_by == "assigned_to_me":
        stmt = stmt.where(
            Task.assignee == current_user.id
        )

    else:
        stmt = stmt.where(
            or_(
                Task.creator == current_user.id,
                Task.assignee == current_user.id
            )
        )

    # Filter by status
    if status == "pending":
        stmt = stmt.where(
            Task.status == "Pending"
        )

    elif status == "in_progress":
        stmt = stmt.where(
            Task.status == "In Progress"
        )

    elif status == "completed":
        stmt = stmt.where(
            Task.status == "Completed"
        )

    stmt = stmt.order_by(Task.deadline) # Order tasks by the closest deadline

    tasks = db.paginate(
        stmt,
        page=page,
        per_page=5
    )

    return render_template(
        "home.html",
        today=date.today(),
        tasks=tasks,
        filter_by=filter_by,
        status=status
    )


@app.route("/about")
def about():
    return render_template(
        "about.html",
        title="About"
    )
#========================== User Routes =================================
@app.route("/register", methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash(
            message="Your account has been created, You can login now.",
            category="success"
        )
        return redirect(url_for("login"))

    return render_template(
        "register.html",
        title="Register",
        form=form
    )


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for("home"))
        else:
            flash("Login failed. Check email and password.", "danger")

    return render_template(
        "login.html",
        title="Login",
        form=form
    )


@app.route("/logout")
@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for("home"))




@app.route("/reset_request", methods=["POST", "GET"])
def request_reset_password():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = Task.query.filter_by(email=form.email.data)
        send_reset_email(user)

    return render_template(
        "reset_request.html",
        title="Reset Password Request",
        form=form
    )


@app.route("/reset_password/<string:token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.verify_reset_token(token)
    # if user is returned then the token is still valid, if not then it's expired or invalid
    if not user:
        flash(
            "Reset token was expired or invalid. Try requesting a new reset.",
            "danger"
        )
        return redirect(url_for("login"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data
        ).decode("utf-8")

        user.password = hashed_password
        db.session.commit()

        flash(
            "Your password has been updated. You can log in now.",
            "success"
        )
        return redirect(url_for("login"))

    return render_template(
        "reset_password.html",
        title="Reset Password",
        legend="Change Password",
        form=form
    )
#=================================================================


#========================================= Task Routes ================================
@app.route("/create_task", methods=["POST", "GET"])
@login_required
def create_task():
    form = TaskForm()
    if form.validate_on_submit():
        if form.assigned_to.data.strip() == "":
            assignee = current_user
        else:
            # assignee existence assured by the form validator
            assignee = User.query.filter_by(username=form.assigned_to.data)

        task = Task(
            title=form.title.data,
            details=form.details.data,
            deadline=form.deadline.data,
            status=form.status.data,
            task_creator=current_user,
            task_assignee=assignee
        )
        db.session.add(task)
        db.session.commit()
        if task.assignee != current_user.id: # create an assignment activity only if the creator isn't the assignee
            activity = Activity(
                type="assignment",
                recipient_id=task.assignee,
                actor_id=current_user.id,
                task_id=task.id
            )
            db.session.add(activity)
            db.session.commit()

        flash(
            message="Task has been created.",
            category="success"
        )
        return redirect(url_for("task", task_id=task.id))

    return render_template(
        "create_task.html",
        title="Create Task",
        legend="Create Task",
        form=form
    )


@app.route("/task/<int:task_id>", methods=["POST", "GET"])
@login_required
def task(task_id):
    task = Task.query.get(task_id)
    form = EmptyForm() # this thr form with submit button to visit the delete task route
    if task:
        return render_template(
            "task.html",
            title=task.title,
            task=task,
            today=date.today(), # this for highlighting overdue tasks
            form=form
        )
    else:
        abort(404)


@app.route("/task/delete/<int:task_id>", methods=["POST", "GET"])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        if task.task_creator == current_user: # Only task creator can delete a task
            db.session.delete(task)
            db.session.commit()
            flash(
                message="Task has been deleted.",
                category="success"
            )
            return redirect(url_for("home"))
        else:
            abort(403)
    else:
        abort(404)


@app.route("/task/edit/<int:task_id>", methods=["POST", "GET"])
@login_required
def edit_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        abort(404)

    if task.task_creator == current_user: # Task editing strictly for task creator only
        form = TaskForm() # re-use the same task form
        form.submit.label.text = "Update"
        if form.validate_on_submit():
            task.title = form.title.data
            task.details = form.details.data
            task.deadline = form.deadline.data
            task.task_assignee = User.query.filter_by(username=form.assigned_to.data)
            task.status = form.status.data
            db.session.commit()
            flash(
                message="Task updated successfully",
                category="success"
            )
            return redirect(url_for("task", task_id=task.id))

        # Pre-fill form fields
        form.title.data = task.title
        form.details.data = task.details
        form.deadline.data = task.deadline
        form.assigned_to.data = task.task_assignee.username
        form.status.data = task.status

        return render_template(
            "create_task.html",
            title="Edit Task",
            legend="Edit Task",
            form=form
        )
    else:
        abort(403) # prevent other than task creator to visit this route


@app.route("/update_task_status/<int:task_id>", methods=["POST", "GET"])
@login_required
def update_task_status(task_id):
    # Assignee and creator have access to this feature
    task = Task.query.get(task_id)
    if task.task_creator == current_user or task.task_assignee == current_user:
        if task.status == "Pending":
            task.status = "In Progress"
            db.session.commit()
            flash(
                message="Task status updated successfully",
                category="success"
            )
            return redirect(url_for("task", task_id=task.id))

        elif task.status == "In Progress":
            task.status = "Completed"
            db.session.commit()

            if task.creator != current_user.id: # Activity: You completed a task assigned to you creator_username
                # current user is the assignee not the creator
                activity = Activity(
                    type="completion",
                    recipient_id=task.creator,
                    actor_id=task.assignee,
                    task_id=task.id
                )
                db.session.add(activity)
                db.session.commit()

            elif task.creator == task.assignee: # Activity: You Completed a Task
                activity = Activity(
                    type="completion",
                    recipient_id=task.assignee,
                    actor_id=task.creator,
                    task_id=task.id
                )
                db.session.add(activity)
                db.session.commit()

            flash(
                message="Task status updated successfully",
                category="success"
            )
            return redirect(url_for("task", task_id=task.id))

        else:
            flash("Task is already completed.", "warning")
            return redirect(url_for("task", task_id=task.id))

    else:
        abort(403)



# ============================ Update Account ================================
@app.route("/account", methods=["POST", "GET"])
@login_required
def account():
    cards = get_cards()
    recent_activities = get_recent_activities()

    return render_template(
        "account.html",
        title="My Account",
        cards=cards,
        activities=recent_activities
    )


@app.route("/update_account", methods=["POST", "GET"])
@login_required
def update_account():
    form = UpdateProfilePicForm()
    if form.validate_on_submit():
        profile_pic = save_picture(form.image_file.data)
        current_user.image_file = profile_pic
        db.session.commit()

    return render_template(
        "update_account.html",
        form=form
    )


@app.route("/change_email", methods=["POST", "GET"])
@login_required
def change_email():
    form = UpdateEmailForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        db.session.commit()
        flash(
            message="Your email address has been changed successfully",
            category="success"
        )
        return redirect(url_for("account"))

    return render_template(
        "update_email.html",
        title="Change Email",
        form=form
    )


@app.route("/change_password", methods=["POST", "GET"])
@login_required
def change_password():
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        # hash the new password and save it in the DB
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        current_user.password = hashed_password
        db.session.commit()
        flash(
            message="Your password has been changed successfully",
            category="success"
        )
        return redirect(url_for("account"))

    return render_template(
        "update_password.html",
        title="Change Password",
        legend="Change Password",
        form=form
    )
#===========================================================================================

#====================================== Errors Pages Routes ======================================
@app.errorhandler(404)
def error_404(error):
    return render_template(
        "errors/404.html",
        title="Page Not Found"
    ), 404


@app.errorhandler(403)
def error_403(error):
    return render_template(
        "errors/403.html",
        title="Permission Not Allowed"
    ), 403


@app.errorhandler(500)
def error_500(error):
    return render_template(
        "errors/500.html",
        title="Page Not Found"
    ), 500