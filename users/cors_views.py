from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View


@csrf_exempt
@require_http_methods(["OPTIONS"])
def cors_preflight(request):
    """
    Handle CORS preflight requests
    """
    response = JsonResponse({}, status=200)
    
    # Add CORS headers
    origin = request.META.get('HTTP_ORIGIN')
    if origin:
        response['Access-Control-Allow-Origin'] = origin
    else:
        response['Access-Control-Allow-Origin'] = '*'
    
    response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    response['Access-Control-Allow-Headers'] = (
        'accept, accept-encoding, authorization, content-type, '
        'dnt, origin, user-agent, x-csrftoken, x-requested-with'
    )
    response['Access-Control-Allow-Credentials'] = 'true'
    response['Access-Control-Max-Age'] = '86400'
    
    return response


class CorsView(View):
    """
    View to handle CORS preflight requests
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def options(self, request, *args, **kwargs):
        """
        Handle OPTIONS requests for CORS preflight
        """
        response = JsonResponse({}, status=200)
        
        # Add CORS headers
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
        else:
            response['Access-Control-Allow-Origin'] = '*'
        
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = (
            'accept, accept-encoding, authorization, content-type, '
            'dnt, origin, user-agent, x-csrftoken, x-requested-with'
        )
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'
        
        return response
