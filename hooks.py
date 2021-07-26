import falcon
from .settings import AUTH_TOKEN
import secrets

AUTH_HEADER = 'WWW-Authenticate'
AUTH_HEADER_VALUE = 'Bearer realm="nyaaaaaa"'


def authenticate(req, resp, resource, params):
    auth = req.get_header('Authorization')
    if not auth or not auth.startswith('Bearer '):
        resp.set_header(AUTH_HEADER, AUTH_HEADER_VALUE)
        raise falcon.HTTPUnauthorized()

    auth = auth.removeprefix('Bearer ')
    if not secrets.compare_digest(auth, AUTH_TOKEN):
        resp.set_header(AUTH_HEADER, AUTH_HEADER_VALUE)
        raise falcon.HTTPUnauthorized()


def evaluate_validation(param_name, value, req, validator):
    if (val_value := validator.validate(value)) is not False:
        req.params[param_name] = val_value
    else:
        raise falcon.HTTPBadRequest(title="400 Bad Request",
                                    description=f"Parameter {param_name} has to be {validator.type}. And "
                                                f"in range of min: {validator.mn}, max: {validator.mx}.")


def validate_params(req, resp, resource, params, validations):

    for val in validations:
        if val['required']:
            value = req.get_param(val['name'])
            if not value:
                raise falcon.HTTPBadRequest(title="400 Bad Request",
                                            description=f"Parameter {val['name']} is missing or empty.")
            if validator := val.get('validator'):
                evaluate_validation(val['name'], value, req, validator)
        else:
            if (value := req.get_param(val['name'])) and (validator := val.get('validator')):
                evaluate_validation(val['name'], value, req, validator)
