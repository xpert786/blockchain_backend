from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Syndicate  # <-- You must import your models

@receiver(post_save, sender=CustomUser)
def create_syndicate_for_manager(sender, instance, created, **kwargs):
    """
    Automatically create a Syndicate when a CustomUser is created
    with role 'syndicate_manager'.
    """
    if created and instance.role == 'syndicate_manager':
        # Create a Syndicate linked to this manager
        Syndicate.objects.create(
            name=f"{instance.username}'s Syndicate",
            manager=instance,
            description=f"Syndicate created automatically for {instance.username}"
        )
