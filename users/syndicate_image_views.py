from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

from .models import CustomUser, Syndicate
from .syndicate_image_models import SyndicateImage


class SyndicateImageViewSet(viewsets.ViewSet):
    """
    ViewSet for managing syndicate images
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @action(detail=False, methods=['post'])
    def upload_image(self, request):
        """
        Upload an image to a syndicate
        POST /api/syndicate-images/upload_image/
        
        Form Data:
        - syndicate_id: ID of the syndicate
        - image: Image file
        - image_type: Type of image (logo, banner, gallery, etc.)
        - title: Optional title for the image
        - description: Optional description
        - alt_text: Optional alt text for accessibility
        - is_primary: Boolean, set as primary image for this type
        """
        syndicate_id = request.data.get('syndicate_id')
        
        if not syndicate_id:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=syndicate_id, manager=request.user)
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if 'image' not in request.FILES:
            return Response({
                'error': 'Image file is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            image_file = request.FILES['image']
            image_type = request.data.get('image_type', 'gallery')
            title = request.data.get('title', '')
            description = request.data.get('description', '')
            alt_text = request.data.get('alt_text', '')
            is_primary = request.data.get('is_primary', 'false').lower() == 'true'
            
            # If this is set as primary, unset other primary images of the same type
            if is_primary:
                SyndicateImage.objects.filter(
                    syndicate=syndicate,
                    image_type=image_type,
                    is_primary=True
                ).update(is_primary=False)
            
            # Create the image record
            syndicate_image = SyndicateImage.objects.create(
                syndicate=syndicate,
                image=image_file,
                image_type=image_type,
                title=title,
                description=description,
                alt_text=alt_text,
                is_primary=is_primary,
                uploaded_by=request.user
            )
            
            return Response({
                'success': True,
                'message': 'Image uploaded successfully',
                'image': {
                    'id': syndicate_image.id,
                    'image_type': syndicate_image.image_type,
                    'title': syndicate_image.title,
                    'description': syndicate_image.description,
                    'alt_text': syndicate_image.alt_text,
                    'is_primary': syndicate_image.is_primary,
                    'uploaded_at': syndicate_image.uploaded_at,
                    'file_size': syndicate_image.file_size,
                    'mime_type': syndicate_image.mime_type,
                    'image_url': syndicate_image.image.url if syndicate_image.image else None
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to upload image: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def get_syndicate_images(self, request):
        """
        Get all images for a syndicate
        GET /api/syndicate-images/get_syndicate_images/?syndicate_id=1&image_type=logo
        """
        syndicate_id = request.query_params.get('syndicate_id')
        image_type = request.query_params.get('image_type')
        
        if not syndicate_id:
            return Response({
                'error': 'syndicate_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=syndicate_id, manager=request.user)
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get images
        images_query = SyndicateImage.objects.filter(syndicate=syndicate, is_active=True)
        
        if image_type:
            images_query = images_query.filter(image_type=image_type)
        
        images = images_query.order_by('-is_primary', '-uploaded_at')
        
        images_data = []
        for image in images:
            images_data.append({
                'id': image.id,
                'image_type': image.image_type,
                'title': image.title,
                'description': image.description,
                'alt_text': image.alt_text,
                'is_primary': image.is_primary,
                'uploaded_at': image.uploaded_at,
                'file_size': image.file_size,
                'mime_type': image.mime_type,
                'image_url': image.image.url if image.image else None
            })
        
        return Response({
            'syndicate_id': syndicate.id,
            'syndicate_name': syndicate.name,
            'images': images_data,
            'total_count': len(images_data)
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def set_primary_image(self, request):
        """
        Set an image as primary for its type
        POST /api/syndicate-images/set_primary_image/
        
        Body:
        {
            "image_id": 1
        }
        """
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response({
                'error': 'image_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            image = SyndicateImage.objects.get(id=image_id, syndicate__manager=request.user)
        except SyndicateImage.DoesNotExist:
            return Response({
                'error': 'Image not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Unset other primary images of the same type
            SyndicateImage.objects.filter(
                syndicate=image.syndicate,
                image_type=image.image_type,
                is_primary=True
            ).update(is_primary=False)
            
            # Set this image as primary
            image.is_primary = True
            image.save()
            
            return Response({
                'success': True,
                'message': f'Image set as primary {image.image_type}',
                'image': {
                    'id': image.id,
                    'image_type': image.image_type,
                    'title': image.title,
                    'is_primary': image.is_primary,
                    'image_url': image.image.url if image.image else None
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to set primary image: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def delete_image(self, request):
        """
        Delete an image
        DELETE /api/syndicate-images/delete_image/
        
        Body:
        {
            "image_id": 1
        }
        """
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response({
                'error': 'image_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            image = SyndicateImage.objects.get(id=image_id, syndicate__manager=request.user)
        except SyndicateImage.DoesNotExist:
            return Response({
                'error': 'Image not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            image_title = image.title or f"{image.image_type} image"
            image.delete()
            
            return Response({
                'success': True,
                'message': f'Image "{image_title}" deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete image: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def update_image_info(self, request):
        """
        Update image information (title, description, alt_text)
        POST /api/syndicate-images/update_image_info/
        
        Body:
        {
            "image_id": 1,
            "title": "New Title",
            "description": "New Description",
            "alt_text": "New Alt Text"
        }
        """
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response({
                'error': 'image_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            image = SyndicateImage.objects.get(id=image_id, syndicate__manager=request.user)
        except SyndicateImage.DoesNotExist:
            return Response({
                'error': 'Image not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Update fields if provided
            if 'title' in request.data:
                image.title = request.data['title']
            if 'description' in request.data:
                image.description = request.data['description']
            if 'alt_text' in request.data:
                image.alt_text = request.data['alt_text']
            
            image.save()
            
            return Response({
                'success': True,
                'message': 'Image information updated successfully',
                'image': {
                    'id': image.id,
                    'image_type': image.image_type,
                    'title': image.title,
                    'description': image.description,
                    'alt_text': image.alt_text,
                    'is_primary': image.is_primary,
                    'image_url': image.image.url if image.image else None
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to update image information: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
