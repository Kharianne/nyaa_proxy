import falcon
from .hooks import authenticate, validate_params
from .nyaa_parser import get_search_results, get_detail, Not200CodeError, PageNotFoundError
import json
from .utils import IntegerValidator

VERSION = '1.0'


class Search:

    @falcon.before(authenticate)
    @falcon.before(validate_params, [{'name': 'q', 'validator': None, 'required': True},
                                     {'name': 'retry', 'validator': IntegerValidator(mn=0), 'required': False},
                                     {'name': 'p', 'validator': IntegerValidator(mn=0), 'required': True}])
    def on_get(self, req, resp):
        q = req.get_param('q')
        page_num = req.get_param('p')
        try:
            if retry := req.get_param('retry'):
                res, next_page = get_search_results(q, page_num, retries=retry)
            else:
                res, next_page = get_search_results(q, page_num)

            doc = {
                'version': VERSION,
                'results': res,
                'next': next_page
            }

            resp.text = json.dumps(doc)

        except PageNotFoundError as e:
            raise falcon.HTTPNotFound(description=str(e))

        except (RuntimeError, Not200CodeError) as e:
            raise falcon.HTTPBadGateway(description=str(e))

        except Exception as e:
            raise falcon.HTTPInternalServerError(description=str(e))


class Detail:

    @falcon.before(authenticate)
    @falcon.before(validate_params, [{'name': 'id', 'validator': IntegerValidator(), 'required': True}])
    def on_get(self, req, resp):
        torrent_id = req.get_param('id')

        try:
            res = get_detail(torrent_id)
            doc = {
                'version': VERSION,
                'result': res
            }

            resp.text = json.dumps(doc)

        except PageNotFoundError as e:
            raise falcon.HTTPNotFound(description=str(e))

        except (RuntimeError, Not200CodeError) as e:
            raise falcon.HTTPBadGateway(description=str(e))

        except Exception as e:
            raise falcon.HTTPInternalServerError(description=str(e))
