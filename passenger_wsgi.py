# -*- coding: utf-8 -*- 
import os, sys
sys.path.insert(0, '/var/www/u1765540/data/www/kirumi.ru/kirumi')
sys.path.insert(1, '/var/www/u1765540/data/djangoenv/lib/python3.10/site-packages')
os.environ['DJANGO_SETTINGS_MODULE'] = 'kirumi.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
