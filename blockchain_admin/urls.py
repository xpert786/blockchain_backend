"""
URL configuration for blockchain_admin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

admin.site.site_header = "Unlocksly"
admin.site.site_title = "Blockchain Administration"
admin.site.index_title = "Welcome to the Blockchain Management Dashboard"

urlpatterns = [
    path('blockchain-backend/admin/', admin.site.urls),
    
    # API endpoints
    path('blockchain-backend/api/', include('users.urls')),
    path('blockchain-backend/api/', include('kyc.urls')),
    path('blockchain-backend/api/', include('spv.urls')),
    path('blockchain-backend/api/', include('documents.urls')),
    path('blockchain-backend/api/', include('transfers.urls')),
    path('blockchain-backend/api/', include('reporting.urls')),
    path('blockchain-backend/api/', include('investors.urls')),
    path('blockchain-backend/api/', include('messaging.urls')),
    
    # JWT token endpoints
    path('blockchain-backend/api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('blockchain-backend/api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('blockchain-backend/api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
