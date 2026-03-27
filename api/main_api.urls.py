from django.urls import path, include
from rest_framework.routers import DefaultRouter
# If you haven't created a View yet, this might show an error, 
# but we'll fix that next if you need.
from .views import * router = DefaultRouter()
# When you make a ViewSet, you will register it here like this:
# router.register(r'items', MyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]