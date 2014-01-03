
Milo Profiler for Django
---

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
