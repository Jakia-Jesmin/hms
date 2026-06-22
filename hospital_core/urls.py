from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Add a simple home view
def home(request):
    return HttpResponse("""
    <html>
        <head>
            <title>Hospital Management System API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #2c3e50; }
                .endpoints { background: #f8f9fa; padding: 20px; border-radius: 5px; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>🏥 Hospital Management System API</h1>
            <p>Welcome to the Hospital Management System API.</p>
            <div class="endpoints">
                <h3>📚 API Documentation:</h3>
                <ul>
                    <li><a href="/api/docs/">Swagger UI</a></li>
                    <li><a href="/api/redoc/">ReDoc</a></li>
                    <li><a href="/api/schema/">OpenAPI Schema</a></li>
                </ul>
                <h3>🔐 Authentication:</h3>
                <ul>
                    <li><a href="/api/auth/login/">POST /api/auth/login/</a></li>
                    <li><a href="/api/auth/register/">POST /api/auth/register/</a></li>
                </ul>
                <h3>📋 API Endpoints:</h3>
                <ul>
                    <li>/api/departments/</li>
                    <li>/api/doctors/</li>
                    <li>/api/patients/</li>
                    <li>/api/appointments/</li>
                    <li>/api/prescriptions/</li>
                    <li>/api/medicines/</li>
                    <li>/api/bills/</li>
                </ul>
            </div>
            <p><a href="/admin/">Admin Panel</a></p>
        </body>
    </html>
    """)

urlpatterns = [
    path('', home, name='home'),  # Add this line for root URL
    path('admin/', admin.site.urls),
    path('api/', include('management.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation with drf-spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)