
Milo Profiler for Django
---

Purpose of this project is to profile views and models using line by line profiler [lineprofiler](http://pythonhosted.org/line_profiler/). Milo Profiler does not display profile during page view but gathers data and stores in [Mongo](http://www.mongodb.org/) database. Those informations can be later analysed using provided client. Main pros of this way of profiling is speed and ability to see how performance varies over requests.

Building steps
===

General:

* install mongo
* git clone this project

In client directory:

* ```npm install```
* ```bower install```

In server directory:

* create virtual env
* ```pip install -r requirements.txt```

In your app directory:

* ```pip install pymongo line-profiler==1.0b3```
* add middleware/middleware.py somewhere in your app and include it in project settings on top of middleware list

Running steps
===

General:

* make some dir for profile database
* ```mongod --dbpath .```

And wait for line like:

```[initandlisten] waiting for connections on port 27017```

This project use default mongod host/port.

In client directory:

* ```grunt serve```

After this step you might have to fix wrong ui-utils path in client/app/index.html ...

In server directory:

* ```gunicorn main:app -w 4 -b :5000```

Run your app and navigate through some pages.
Visit http://localhost:9000/
