from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings


class CustomCorsMiddleware(MiddlewareMixin):
    """
    Custom CORS middleware that handles preflight requests properly
    """
    
    def process_request(self, request):
        # Handle preflight requests immediately
        if request.method == 'OPTIONS':
            response = JsonResponse({}, status=200)
            self.add_cors_headers(response, request)
            return response
    
    def process_response(self, request, response):
        # Add CORS headers to all responses
        self.add_cors_headers(response, request)
        return response
    
    def add_cors_headers(self, response, request):
        origin = request.META.get('HTTP_ORIGIN')
        
        # Check if origin is allowed
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        allow_all_origins = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)
        
        # For development, allow all origins
        if allow_all_origins or origin in allowed_origins or origin:
            response['Access-Control-Allow-Origin'] = origin or '*'
        
        # Add other CORS headers
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = (
            'accept, accept-encoding, authorization, content-type, '
            'dnt, origin, user-agent, x-csrftoken, x-requested-with'
        )
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'
        
        return response
