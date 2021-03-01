from flask import Flask, request, jsonify, abort
from sqlalchemy.orm.exc import NoResultFound
import json
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# db_drop_and_create_all()

# Custom error for invalid request body


class RequestBodyError(Exception):

    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def validate_body(body):
    if not body or ('title' not in body and 'recipe' not in body):
        raise RequestBodyError({
            'code': 'Request body error',
            'description': 'Request body was empty or valid keys are missing'
            }, 400)

    return True


# ROUTES

@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks_query = Drink.query.order_by('id').all()
    drinks = [drink.short() for drink in drinks_query]

    if len(drinks) == 0:
        raise NoResultFound

    return jsonify({
        'success': True,
        'drinks': drinks
    })


@app.route('/drinks-detail', methods=['GET'])
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail(payload):
    drinks_query = Drink.query.order_by('id').all()
    drinks = [drink.long() for drink in drinks_query]

    if len(drinks) == 0:
        raise NoResultFound

    return jsonify({
        'success': True,
        'drinks': drinks
    })


@app.route('/drinks', methods=['POST'])
@requires_auth(permission='post:drink')
def create_drink(payload):
    body = request.get_json()
    validate_body(body)
    print(body)
    try:
        drink_title = body['title']
        drink_recipe = body['recipe'] if type(body['recipe']) == str \
            else json.dumps(body['recipe'])
        drink = Drink(title=drink_title, recipe=drink_recipe)
        print(drink)
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })

    except Exception:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth(permission='patch:drink')
def modify_drink(payload, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one()
    body = request.get_json()
    validate_body(body)

    try:
        if not body or ('title' not in body and 'recipe' not in body):
            raise RequestBodyError

        if 'title' in body:
            drink.title = body['title']

        if 'recipe' in body:
            drink.recipe = body['recipe'] if type(body['recipe']) == str \
                else json.dumps(body['recipe'])

        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })

    except Exception:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth(permission='delete:drink')
def delete_drink(payload, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one()

    try:
        drink.delete()

        return jsonify({
            'success': True,
            'delete': drink_id
        })

    except Exception:
        abort(422)


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
        }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
        }), 404


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
        }), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "forbidden"
        }), 403


@app.errorhandler(AuthError)
def auth_error_handler(error):
    return jsonify({
        "success": False,
        "error": error.error['code'],
        "message": error.error['description']
        }), error.status_code


@app.errorhandler(RequestBodyError)
def request_body_error(error):
    return jsonify({
        "success": False,
        "error": error.error['code'],
        "message": error.error['description']
        }), error.status_code


@app.errorhandler(NoResultFound)
def no_drink_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": 'The drink(s) could not be found'
        }), 404


@app.errorhandler(BadRequest)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": 'Bad request'
        }), 400
