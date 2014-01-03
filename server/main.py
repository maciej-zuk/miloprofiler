from flask import Flask, make_response
from flask.ext import restful
import pymongo
import json
import bson
from bson import json_util
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter


class CustomHtmlFormatter(HtmlFormatter):
    """
        Custom HtmlFormatter with lines separated by ``\0`` without wrapping.
    """
    def _wrap_code(self, source):
        yield 0, ''
        for i, t in source:
            yield i, t+'\0'
        yield 0, ''

    def wrap(self, source, outfile):
        return self._wrap_code(source)


class RequestsResource(restful.Resource):
    def get(self, oid=None):
        if oid:
            try:
                obj_id = bson.objectid.ObjectId(oid)
            except bson.objectid.InvalidId:
                return None, 400
            request = requests_collection.find_one({'_id': obj_id})
            return request
        else:
            result = []
            for rq in requests_collection.find(sort=[('start', pymongo.ASCENDING)]):
                result.append(rq)
            return result


class TimingsResource(restful.Resource):
    def get(self, oid=None):
        if oid:
            try:
                obj_id = bson.objectid.ObjectId(oid)
            except bson.objectid.InvalidId:
                return None, 400
            timing = timings_collection.find_one({'_id': obj_id})

            data = None

            #first and last line of timed function
            firstline = timing["file_lineno"] - 1 #add function def
            lastline = firstline
            for shot in timing['timings']:
                cline = shot["data"][-1][0]
                if cline > lastline:
                    lastline = cline
            try:
                source = open(timing["file_name"])
                data = {}
                lines = []
                for lineno, line in enumerate(source):
                    if lineno < firstline:
                        continue
                    if lineno > lastline:
                        break
                    lines.append(line)

                #highlight selected lines, we need to join them to let pygments treat code as a whole thing
                highlighted = highlight("".join(lines), lexer, formatter)

                #split again for futher processing
                for offset, line in enumerate(highlighted.split('\0')[:-1]):
                    source_line = {
                        'html': line,
                        'requests': []
                    }
                    data[firstline+offset+1] = source_line
            except IOError:
                pass

            #we have highlighted source code in data
            if data:
                #process each request timing
                for shot in timing['timings']:
                    obj_id = bson.objectid.ObjectId(shot['rq_id'])
                    rq_path = requests_collection.find_one({'_id': obj_id}, fields={'path': True})['path']
                    for lineno, hits, time in shot["data"]:
                        if not lineno in data:
                            continue
                        rq_hit = {
                            'request': rq_path,
                            'hits': hits,
                            'timing': time/1000.0
                        }
                        data[lineno]["requests"].append(rq_hit)

                #add mean values and total requests count for line, place lines in order
                lines = []
                data_lines = list(data.items())
                data_lines.sort()
                for lineno, line in data_lines:
                    if line["requests"]:
                        requests = line["requests"]
                        rq_count = float(len(requests))
                        line["hits"] = sum([x['hits'] for x in requests]) / rq_count
                        line["timing"] = sum([x['timing'] for x in requests]) / rq_count
                        line["rqs"] = rq_count
                    line["number"] = lineno
                    lines.append(line)
                data = lines

            # timings no longer needed, pushed into data
            del timing['timings']

            timing['data'] = data
            return timing
        else:
            result_data = {}
            fields = {'timings': False}

            #group timings by filename
            for timing in timings_collection.find(fields=fields, sort=[('file_lineno', pymongo.ASCENDING)]):
                file_name = timing["file_name"]
                if not file_name in result_data:
                    result_data[file_name] = []
                del timing["file_name"]
                result_data[file_name].append(timing)

            result = []
            for file_name, timings in result_data.iteritems():
                value = {
                    'file_name': file_name,
                    'data': timings
                }
                result.append(value)
            return result


app = Flask(__name__, static_url_path='')
api = restful.Api(app)


@app.route('/')
def root():
    return app.send_static_file('index.html')


#add cors to reponses
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data, default=json_util.default), code)
    resp.headers.extend(headers or {})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

#prepare database
requests_collection = pymongo.MongoClient().profiles.requests
requests_collection.create_index([("start", pymongo.ASCENDING)])
timings_collection = pymongo.MongoClient().profiles.timings
timings_collection.create_index([("file_lineno", pymongo.ASCENDING)])

#prepare pygments for future usage
lexer = PythonLexer()
formatter = CustomHtmlFormatter()

#add resources endpoints
api.add_resource(RequestsResource, '/requests/<string:oid>', endpoint='requests.detail')
api.add_resource(RequestsResource, '/requests', endpoint='requests')
api.add_resource(TimingsResource, '/timings/<string:oid>', endpoint='timings.detail')
api.add_resource(TimingsResource, '/timings', endpoint='timings')

if __name__ == '__main__':
    app.run(debug=True)
