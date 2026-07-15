from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required
)
from taskmanager import api, db, bcrypt
from flask_restful import Resource, fields, reqparse, marshal_with, marshal
from flask import request
from taskmanager.models import User, Task
from sqlalchemy import or_
from taskmanager.utils import is_valid_email, parse_date


#============================== Register/Login =================================
# Handle registration
class RegisterAPI(Resource):
    def post(self):
        data = request.get_json()
        if not data.get("username") or not data.get("email") or not data.get("password"):
            return {'error': 'Username, email and password are required'}, 400

        if not is_valid_email(data["email"]):
            return {"error": "Email address is invalid"}

        if User.query.filter_by(email=data["email"]).first():
            return ({'error': 'There is already an account register with this email address'}), 400

        if User.query.filter_by(username=data["username"]).first():
            return {'error': 'Username is already taken'}, 400

        hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        user = User(
            email=data["email"],
            username=data["username"],
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()

        return {'message': f"Account created for {user.username}"}, 201


# Handle Login and return JWT
class LoginAPI(Resource):
    def post(self):
        data = request.get_json()

        if not data.get("email") or not data.get("password"):
            return ({'error': 'Email and password are required'}), 400

        user = User.query.filter_by(email=data["email"]).first()

        # Authenticating the user credentials
        if not user or not bcrypt.check_password_hash(user.password, data["password"]):
            return {'error': 'Invalid email or password'}, 401

        access_token = create_access_token(identity=str(user.id))

        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        }, 200

#================================================================================

#=================================== Fields Parsing =============================
# for serializing task object into JSON
task_fields = {
    "id": fields.Integer,
    "title": fields.String,
    "details": fields.String,
    "status": fields.String,
    "deadline": fields.String,
    "creator": fields.Integer,
    "assignee": fields.Integer
}

# Adding a parser to parse request data and validate it
task_parser = reqparse.RequestParser()
task_parser.add_argument("title", type=str, required=True, help="Title is a required field")
task_parser.add_argument("status", type=str, required=False)
task_parser.add_argument("deadline", type=parse_date, required=False, help="Deadline must be in YYYY-MM-DD format")
task_parser.add_argument("details", type=str, required=False)
task_parser.add_argument("assignee", type=int, required=False)
#================================================================================

#===================================== Tasks Endpoints ==========================
class TasksAPI(Resource):
    @marshal_with(task_fields)
    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())

        # User can only access tasks he created or assigned to him
        tasks = db.session.scalars(
            db.select(Task).where(
                or_(Task.creator == user_id, Task.assignee == user_id)
            )
        ).all()

        return tasks

    @marshal_with(task_fields)
    @jwt_required()
    def post(self):
        user_id = int(get_jwt_identity())

        task_data = task_parser.parse_args()
        if task_data["assignee"] is None:
            task_data["assignee"] = user_id

        # Standardization
        if task_data["status"] is None:
            task_data["status"] = "Pending"

        elif task_data["status"] == "pending":
            task_data["status"] = "Pending"

        elif task_data["status"] == "completed":
            task_data["status"] = "Completed"


        task = Task(
            title=task_data["title"],
            details=task_data["details"],
            status=task_data["status"],
            deadline=task_data["deadline"],
            creator=user_id,
            assignee=task_data["assignee"]
        )
        db.session.add(task)
        db.session.commit()
        return task, 201


class TaskAPI(Resource):

    @jwt_required()
    def get(self, task_id):
        user_id = int(get_jwt_identity())

        task = db.session.scalar(
            db.select(Task).where(Task.id == task_id)
        )
        if not task:
            return {"message": "Task wasn't found"}, 404

        # User can only access tasks he created or assigned to him
        if task.creator != user_id and task.assignee != user_id:
            return {'error': 'Access denied'}, 403

        return marshal(task, task_fields), 200

    @jwt_required()
    def delete(self, task_id):
        user_id = int(get_jwt_identity())

        task = db.session.scalar(
            db.select(Task).where(Task.id == task_id)
        )
        if not task:
            return {"message": "Task wasn't found"}, 404

        if task.creator != user_id: # ensure only creator can delete the task
            return {'error': 'Access denied'}, 403

        db.session.delete(task)
        db.session.commit()
        return {"message": "Task deleted successfully"}, 200


    @jwt_required()
    def patch(self, task_id):
        user_id = int(get_jwt_identity())

        task_data = request.get_json()
        if not task_data.get("status"):
            return {"error": "New status must be provided"}, 400

        task = db.session.scalar(
            db.select(Task).where(Task.id == task_id)
        )

        if not task:
            return {"message": "Task wasn't found"}, 404

        if task.creator != user_id and task.assignee != user_id:
            return {'error': 'Access denied'}, 403

        task.status = task_data["status"]
        db.session.commit()
        return marshal(task, task_fields), 200


class TasksByStatusAPI(Resource):
    @jwt_required()
    def get(self, status):
        user_id = int(get_jwt_identity())

        status_map = {
            "pending": "Pending",
            "in-progress": "In Progress",
            "completed": "Completed"
        }

        if status not in status_map.keys():
            return {"error": "Invalid status was provided"}, 400

        status_cleaned = status_map["status"]

        tasks = db.session.scalars(
            db.select(Task).where(
                or_(Task.creator == user_id, Task.assignee == user_id),
                Task.status == status_cleaned
            )
        ).all()

        return  marshal(tasks, task_fields), 200


class AssignedTasks(Resource):
    @marshal_with(task_fields)
    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())

        tasks = db.session.scalars(
            db.select(Task).where(
                Task.assignee == user_id
            )
        ).all()

        return tasks


class CreatedTasks(Resource):
    @marshal_with(task_fields)
    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())

        tasks = db.session.scalars(
            db.select(Task).where(
            Task.creator == user_id
            )
        ).all()

        return tasks



# adding the endpoints
api.add_resource(RegisterAPI, "/api/register")
api.add_resource(LoginAPI, "/api/login")
api.add_resource(TasksAPI, "/api/tasks")
api.add_resource(TaskAPI, "/api/tasks/<int:task_id>")
api.add_resource(TasksByStatusAPI, "/api/tasks/filter/<string:status>")
api.add_resource(AssignedTasks, "/api/tasks/assigned_tasks")
api.add_resource(CreatedTasks, "/api/tasks/created_tasks")