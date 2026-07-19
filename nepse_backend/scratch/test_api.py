import os
import sys
import django

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nepse_backend.settings")
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

from django.contrib.auth.models import User
from rest_framework.test import APIClient


# Ensure we have a test user
user, created = User.objects.get_or_create(username="api_test_user")
if created:
    user.set_password("testpass123")
    user.save()

client = APIClient()
client.force_authenticate(user=user)

print("--- Testing Stock Fundamentals API ---")
response = client.get("/api/stocks/NABIL/fundamentals/")
print("Status Code:", response.status_code)
print("Data:")
import json
print(json.dumps(response.data, indent=2))

print("\n--- Testing Sectors Summary API ---")
response = client.get("/api/stocks/sectors/summary/")
print("Status Code:", response.status_code)
print("Data (first 3 sectors):")
print(json.dumps(response.data[:3], indent=2))

print("\n--- Testing Confluence Signals API ---")
response = client.get("/api/signals/confluence/")
print("Status Code:", response.status_code)
print("Data (first 3 stocks):")
print(json.dumps(response.data[:3], indent=2))

