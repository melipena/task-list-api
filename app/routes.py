from flask import Blueprint
from flask import Blueprint, jsonify, request, abort, make_response
from app import db
from app.models.task import Task
from app.models.goal import Goal 
from datetime import datetime
import requests
import os

tasks_bp = Blueprint("tasks", __name__,url_prefix="/tasks")

# Helper function
def get_model_from_id(cls, model_id):
    try:
        model_id = int(model_id)
    except ValueError:
        return abort(make_response({"msg": f"invalid data type: {model_id}"}, 200))


    chosen_task = cls.query.get(model_id)

    if chosen_task is None:
        return abort(make_response({"msg": f"Could not find the task with id: {model_id}"}, 404))
    
    return chosen_task

@tasks_bp.route('', methods=['POST'])
def create_one_task():
    request_body = request.get_json()
    if "title" not in request_body or "description" not in request_body:
        return abort(make_response({"details": "Invalid data"}, 400))

    new_task= Task(title=request_body["title"],
                description=request_body["description"]

    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({"task":new_task.to_dict()}), 201

@tasks_bp.route('', methods=['GET'])
def get_all_tasks():

    sort_query_value = request.args.get('sort')
    if sort_query_value == "desc":
        tasks = Task.query.order_by(Task.title.desc()).all() 
    else:
    
        tasks = Task.query.order_by(Task.title.asc()).all()

    result = []

    for task in tasks:
        result.append(task.to_dict())
    
    return jsonify(result), 200

@tasks_bp.route('/<task_id>', methods=['GET'])
def get_one_task(task_id):

    chosen_task = get_model_from_id(Task, task_id)

    return jsonify({"task":chosen_task.to_dict()}), 200

@tasks_bp.route('/<task_id>', methods=['PUT'])
def update_one_task(task_id):
    update_task = get_model_from_id(Task, task_id)

    request_body = request.get_json()

    try:
        update_task.title = request_body["title"]
        update_task.description = request_body["description"]

    except KeyError:
        return jsonify ({"msg": f"Missing attributes"}), 400

    db.session.commit()
    return jsonify({"task":update_task.to_dict()})

@tasks_bp.route('/<task_id>', methods=['DELETE'])
def delete_one_task(task_id):
    task_to_delete = get_model_from_id(Task, task_id)

    title_task_to_delete= get_model_from_id(Task, task_id).to_dict()["title"]

    db.session.delete(task_to_delete)
    db.session.commit()

    return jsonify({"details": f'Task {task_id} "{title_task_to_delete}" successfully deleted'}), 200
        
@tasks_bp.route('/<task_id>/mark_complete', methods=['PATCH'])
def mark_complete_on_an_incompleted_task(task_id):
    current_time = datetime.now()
    patch_task = get_model_from_id(Task, task_id)
    patch_task.completed_at = current_time

    db.session.commit()

    TOKEN_SLACK = os.environ.get("GIVEN_TOKEN_SLACK")
    params = {"text": f"Someone just completed the task {patch_task.title}",
                    "channel": "task-notifications"}
    
    headers = {"Authorization": "Bearer "+ TOKEN_SLACK}

    requests.post(url='https://slack.com/api/chat.postMessage',json=params, headers=headers)

    return jsonify({"task":patch_task.to_dict()}), 200

@tasks_bp.route('/<task_id>/mark_incomplete', methods=['PATCH'])
def mark_incomplete_on_an_completed_task(task_id):
    current_time = None 
    patch_task = get_model_from_id(Task, task_id)
    patch_task.completed_at = current_time

    db.session.commit()

    return jsonify({"task":patch_task.to_dict()}), 200

