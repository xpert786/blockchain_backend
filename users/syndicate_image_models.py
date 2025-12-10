from django.db import models
from django.conf import settings
import os


def syndicate_image_upload_path(instance, filename):
    """Generate upload path for syndicate images"""
    return f'syndicate_images/{instance.syndicate.id}/{instance.image_type}/{filename}'


class SyndicateImage(models.Model):
    """Model for storing syndicate images"""
    
    IMAGE_TYPES = [
        ('logo', 'Logo'),
        ('banner', 'Banner'),
        ('gallery', 'Gallery'),
        ('document', 'Document'),
        ('certificate', 'Certificate'),
        ('team_photo', 'Team Photo'),
        ('office_photo', 'Office Photo'),
        ('other', 'Other'),
    ]
    
    syndicate = models.ForeignKey('users.SyndicateProfile', on_delete=models.CASCADE, related_name='images')
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPES, default='gallery')
    image = models.ImageField(upload_to=syndicate_image_upload_path)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)  # For logo/banner selection
    is_active = models.BooleanField(default=True)
    file_size = models.BigIntegerField(blank=True, null=True)  # File size in bytes
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = 'syndicate image'
        verbose_name_plural = 'syndicate images'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.syndicate.firm_name or self.syndicate.user.username} - {self.get_image_type_display()}"
    
    def save(self, *args, **kwargs):
        if self.image:
            self.file_size = self.image.size
            self.mime_type = getattr(self.image, 'content_type', 'image/jpeg')
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete the file from storage when the model is deleted
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)
