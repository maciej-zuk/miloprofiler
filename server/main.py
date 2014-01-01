from flask import Flask
from flask.ext import restful
import pymongo

app = Flask(__name__)
api = restful.Api(app)

rq_db = pymongo.MongoClient().profiles.requests


class RequestsResource(restful.Resource):

    def get(self):
        result = []
        for rq in rq_db.find():
            del rq["_id"]
            result.append(rq)
        return result

api.add_resource(RequestsResource, '/rq')

if __name__ == '__main__':
    app.run(debug=True)
