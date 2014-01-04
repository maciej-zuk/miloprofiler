import line_profiler
import time
import re
import os
import pymongo
import urls
from django.db import models
from django.conf import settings

try:
    proj_name = settings.PROJECT_ROOT.split(os.path.sep)[-1]
    client = pymongo.MongoClient()
    timings_db = client['profiles_%s' % proj_name].timings
    requests_db = client['profiles_%s' % proj_name].requests
    ready = True
except:
    ready = False

cname_re = re.compile(".*?((?:[a-z][a-z\\.\\d\\-]+)\\.(?:[a-z][a-z\\-]+))(?![\\w\\.])", re.IGNORECASE | re.DOTALL)


def str_from_klass(klass):
    m = cname_re.match(str(klass))
    if m:
        return m.group(1)
    else:
        return str(klass)


def extract_functions(klass):
    fns = []
    for x in dir(klass):
        try:
            attr = getattr(klass, x)
        except:
            continue
        if hasattr(attr, '__code__'):
            fns.append(attr)
    return fns


def prepare_functions_from_url(urllist):
    function_list = []
    classmap = {}
    for entry in urllist:

        func = entry.callback
        if func is None:
            continue
        if hasattr(func, '__code__'):
            code = func.__code__
            label = (code.co_filename, code.co_firstlineno, code.co_name)
            function_list.append(func)
            if hasattr(func, 'im_class'):
                classmap[label] = str_from_klass(func.im_class)
            else:
                classmap[label] = "function"

        if hasattr(func, '__closure__') and func.__closure__:
            for cell in func.__closure__:
                if type(cell.cell_contents) == type:
                    for elm in extract_functions(cell.cell_contents):
                        if hasattr(elm, '__code__'):
                            code = elm.__code__
                            label = (code.co_filename, code.co_firstlineno, code.co_name)
                            classmap[label] = str_from_klass(cell.cell_contents)
                            function_list.append(func)

        if hasattr(entry, 'url_patterns'):
            fl, cmap = prepare_functions_from_models(entry.url_patterns)
            function_list.extend(fl)
            classmap.update(cmap)
    return function_list, classmap


def prepare_functions_from_models():
    function_list = []
    classmap = {}
    for model in models.get_models():
        for elm in extract_functions(model):
            if hasattr(elm, '__code__'):
                code = elm.__code__
                label = (code.co_filename, code.co_firstlineno, code.co_name)
                classmap[label] = str_from_klass(model)
                function_list.append(elm)
        for elm in extract_functions(model.objects):
            if hasattr(elm, '__code__'):
                code = elm.__code__
                label = (code.co_filename, code.co_firstlineno, code.co_name)
                classmap[label] = str_from_klass(model.objects)
                function_list.append(elm)
    return function_list, classmap

prepared_classmap = {}
prepared_function_list = []

if ready:
    models_flist, models_cmap = prepare_functions_from_models()
    urls_flist, urls_cmap = prepare_functions_from_url(urls.urlpatterns)
    prepared_classmap.update(models_cmap)
    prepared_classmap.update(urls_cmap)
    prepared_function_list.extend(models_flist)
    prepared_function_list.extend(urls_flist)


class MiloProfiler(object):
    def process_request(self, request):
        if ready is False:
            return
        self.lp = line_profiler.LineProfiler()
        for func in prepared_function_list:
            self.lp.add_function(func)
        self.lp.enable()
        self.rq_time_start = time.time()

    def process_response(self, request, response):
        if ready is False:
            return response
        self.rq_time_end = time.time()
        self.lp.disable()
        proj_prefix = settings.PROJECT_ROOT
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
                    'classname': prepared_classmap.get(fn, 'unknown'),
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
                'classname': prepared_classmap.get(fn, 'unknown'),
                'file_lineno': fn_line
            }
            requests_db.update({'_id': rq_id}, {'$push': {'timings': timing_short}})

        return response
