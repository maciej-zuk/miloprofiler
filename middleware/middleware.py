import line_profiler
import time
import re
from django.conf import settings
import pymongo
import urls
from django.db import models

try:
    client = pymongo.MongoClient()
    timings_db = client.profiles.timings
    requests_db = client.profiles.requests
    ready = True
except:
    ready = False

cname_re = re.compile(".*?((?:[a-z][a-z\\.\\d\\-]+)\\.(?:[a-z][a-z\\-]+))(?![\\w\\.])", re.IGNORECASE | re.DOTALL)


class MiloProfiler(object):

    def str_from_klass(self, klass):
        m = cname_re.match(str(klass))
        if m:
            return m.group(1)
        else:
            return str(klass)

    def extract_functions(self, klass):
        fns = []
        for x in dir(klass):
            try:
                attr = getattr(klass, x)
            except:
                continue
            if hasattr(attr, '__code__'):
                fns.append(attr)
        return fns

    def add_urls(self, urllist, depth=0):
        for entry in urllist:

            func = entry.callback
            if func is None:
                continue
            if hasattr(func, '__code__'):
                code = func.__code__
                label = (code.co_filename, code.co_firstlineno, code.co_name)
                self.lp.add_function(func)
                if hasattr(func, 'im_class'):
                    self.label2class[label] = self.str_from_klass(func.im_class)
                else:
                    self.label2class[label] = "function"

            if hasattr(func, '__closure__'):
                for cell in func.__closure__:
                    if type(cell.cell_contents) == type:
                        for elm in self.extract_functions(cell.cell_contents):
                            if hasattr(elm, '__code__'):
                                code = elm.__code__
                                label = (code.co_filename, code.co_firstlineno, code.co_name)
                                self.label2class[label] = self.str_from_klass(cell.cell_contents)
                                self.lp.add_function(elm)

            if hasattr(entry, 'url_patterns'):
                self.add_urls(entry.url_patterns, depth + 1)

    def add_models(self):
        for model in models.get_models():
            for elm in self.extract_functions(model):
                if hasattr(elm, '__code__'):
                    code = elm.__code__
                    label = (code.co_filename, code.co_firstlineno, code.co_name)
                    self.label2class[label] = self.str_from_klass(model)
                    self.lp.add_function(elm)
            for elm in self.extract_functions(model.objects):
                if hasattr(elm, '__code__'):
                    code = elm.__code__
                    label = (code.co_filename, code.co_firstlineno, code.co_name)
                    self.label2class[label] = self.str_from_klass(model.objects)
                    self.lp.add_function(elm)

    def process_request(self, request):
        if ready is False:
            return
        self.label2class = {}
        self.rq_time_start = time.time()
        self.lp = line_profiler.LineProfiler()
        self.add_urls(urls.urlpatterns)
        self.add_models()
        self.lp.enable()

    def process_response(self, request, response):
        if ready is False:
            return
        self.rq_time_end = time.time()
        proj_prefix = settings.PROJECT_ROOT
        self.lp.disable()
        rq_path = request.get_full_path()
        rq_data = {
            'start': self.rq_time_start,
            'duration': max(0, self.rq_time_end - self.rq_time_start),
            'path': rq_path,
            'calls': [],
            'timings': [],
        }
        rq_id = requests_db.insert(rq_data)

        for fn, timings in self.lp.get_stats().timings.iteritems():
            file_name, fn_line, f_name = fn

            #catch only calls within project
            if not file_name.startswith(proj_prefix):
                continue

            #no call for this function
            if len(timings) == 0:
                continue

            #find existing timing for update
            existing_timing = timings_db.find_one({'file_name': file_name, 'file_lineno': fn_line, 'file_function': f_name})
            if existing_timing:
                timing_shot = {
                    'rq_id': str(rq_id),
                    'data': timings
                }
                timings_db.update({'_id': existing_timing["_id"]}, {'$push': {'timings': timing_shot}})
                timing_id = existing_timing['_id']
            else:
                timing = {
                    'file_name': file_name,
                    'file_function': f_name,
                    'file_lineno': fn_line,
                    'classname': self.label2class[fn],
                    'timings': [{
                        'rq_id': str(rq_id),
                        'data': timings
                    }]
                }
                timing_id = timings_db.insert(timing)

            #update request with timings info
            timing_short = {
                'id': str(timing_id),
                'file_name': file_name,
                'file_function': f_name,
                'classname': self.label2class[fn],
                'file_lineno': fn_line
            }
            requests_db.update({'_id': rq_id}, {'$push': {'timings': timing_short}})

        return response
