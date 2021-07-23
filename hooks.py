import falcon
from .settings import AUTH_TOKEN
from .utils import constant_time_compare


def authorization(req, resp, resource, params):
    auth = req.get_header('Authorization')
    if not auth or not auth.startswith('Bearer '):
        resp.set_header('WWW-Authenticate', 'Bearer realm="nyaaaaaa"')
        raise falcon.HTTPUnauthorized()

    auth = auth.removeprefix('Bearer ')
    if not constant_time_compare(auth, AUTH_TOKEN):
        resp.set_header('WWW-Authenticate', 'Bearer realm="nyaaaaaa"')
        raise falcon.HTTPUnauthorized()


def validate_params(req, resp, resource, params, validations):

    def validate_type_and_value(param_name, value, _type):
        try:
            req.params[param_name] = _type(value)
        except (ValueError, TypeError):
            raise falcon.HTTPBadRequest(title="400 Bad Request",
                                        description=f"Parameter {param_name} has to be {_type}. "
                                                    f"{type(value)} given.")
        else:
            if not req.params[param_name] >= 0:
                raise falcon.HTTPBadRequest(title="400 Bad Request",
                                            description=f"Parameter {param_name} has to be 0 or greater. "
                                                        f"{value} given.")

    for val in validations:
        if val['required']:
            value = req.get_param(val['name'])
            if not value:
                raise falcon.HTTPBadRequest(title="400 Bad Request",
                                            description=f"Parameter {val['name']} is missing or empty.")
            if val['value_type']:
                validate_type_and_value(val['name'], value, val['value_type'])

        else:
            if (value := req.get_param(val['name'])) and val['value_type']:
                validate_type_and_value(val['name'], value, val['value_type'])
