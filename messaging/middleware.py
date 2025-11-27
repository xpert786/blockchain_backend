"""
Authentication middleware for WebSocket connections
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    
    Token can be passed via:
    1. Query parameter: ws://localhost:8000/ws/chat/1/?token=YOUR_JWT_TOKEN
    2. Cookie: if token is stored in cookies
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query string or headers
        token = None
        
        # Try to get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        if 'token' in query_params:
            token = query_params['token'][0]
        
        # If no token in query string, try to get from cookies
        if not token:
            headers = dict(scope.get('headers', []))
            cookie_header = headers.get(b'cookie', b'').decode()
            
            if cookie_header:
                cookies = {}
                for cookie in cookie_header.split('; '):
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        cookies[key] = value
                
                token = cookies.get('access_token') or cookies.get('token')
        
        # Authenticate user with token
        if token:
            scope['user'] = await self.get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_token(self, token_string):
        """
        Validate JWT token and return the user.
        """
        try:
            # Decode the token
            access_token = AccessToken(token_string)
            
            # Get user_id from token
            user_id = access_token.get('user_id')
            
            # Fetch user from database
            user = User.objects.get(id=user_id)
            return user
            
        except (InvalidToken, TokenError, User.DoesNotExist) as e:
            # Invalid token or user doesn't exist
            return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Alternative: Simple token authentication middleware.
    For session-based authentication, this allows connection without JWT.
    """
    
    async def __call__(self, scope, receive, send):
        # For development, you can allow all connections
        # Comment this out in production
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get first user for testing (REMOVE IN PRODUCTION)
        scope['user'] = await self.get_first_user()
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_first_user(self):
        """Get first user for testing purposes."""
        User = get_user_model()
        try:
            return User.objects.first()
        except:
            return AnonymousUser()
 