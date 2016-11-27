# Installation
These installation instructions are for Ubuntu 14.04+ only.

## Python dependencies
This system runs on the Python Flask framework which has a number of dependencies of its own, most of which are handled
 by package managers like PIP.

Python packages:
    * flask
    * rdflib
    * lxml (installed by rdflib dependencies)
    * requests (installed by rdflib dependencies)

> pip install flask
> pip install rdflib


## Apache2
Install Apache and a series of Apache modules

> sudo aptitude install -y apache2
> sudo a2enmod xml2enc proxy proxy_html proxy_http

Configure Apache to point to the IGSN API

> sudo nano /etc/apache2/sites-available/000-default.conf
# replace contents with apache.conf in this folder (modify paths accordingly)




