from django.contrib import admin
from django.urls import include, path

from api.views import redirect_short_url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_link>/', redirect_short_url, name='recipe_redirect'),
]
