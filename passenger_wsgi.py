import os
import sys

from django.core.wsgi import get_wsgi_application

# Add project directory to the sys.path
cwd = os.getcwd()
sys.path.append(cwd)

# Point to your django application module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

application = get_wsgi_application()
