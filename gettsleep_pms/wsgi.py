import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gettsleep_pms.settings')
application = get_wsgi_application()
