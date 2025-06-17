from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('app/', include('service_manager.urls')),
    # Potentially a root path redirecting to the app or a dashboard
    # path('', some_view_for_root, name='home'),
]
