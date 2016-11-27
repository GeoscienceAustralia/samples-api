# Running the API in test and prod modes
This API, which runs on Python Flask, can either be served up (HTTP) using
Flask's in-built test web server or by some other web server with a WSGI 
(Python container gateway interface) module.


## Test mode
If running this API via Flask's in-built web server, code changes will 
instantly be applied to the running instance. The API will have to be run
on a port different to any web servers (the default in port 9000) and proxied
to by a web server (such as Apache, nginx) if BASIC security and nice paths
are required.

To run in test mode:

* just run # python app.py at the command line and adjust settings in
settings.py appropriately.


## Production mode
If running this API as a WSGI module from a web server (Apache, nginx), code 
changes will need a web server restart to be propagated to a running instance.

To run in prod mode:

* install Apache's mod_wsgi
    * you may need to get the module: # sudo aptitude install libapache2-mod-wsgi
    * # sudo a2enmod wsgi
* configure the *.wsgi file
    * igsn-ld-api.wsgi: replace variables ({{}}) with values from settings.py
* configure Apache
    * adapt the file apache.conf with values from settings.py
   