import os
import sys

# Get the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the Django project folder to Python path
sys.path.append(os.path.join(BASE_DIR, "demo"))

# Tell Django where settings.py is located
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()