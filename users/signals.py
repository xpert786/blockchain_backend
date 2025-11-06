from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, SyndicateProfile  # <-- Updated to use SyndicateProfile

@receiver(post_save, sender=CustomUser)
def create_syndicate_profile_for_syndicate_user(sender, instance, created, **kwargs):
    """
    Automatically create a SyndicateProfile when a CustomUser is created
    with role 'syndicate'.
    """
    if created and instance.role == 'syndicate':
        # Create a SyndicateProfile linked to this user
        SyndicateProfile.objects.create(
            user=instance,
            firm_name=f"{instance.username}'s Firm",
            description=f"Syndicate profile created automatically for {instance.username}"
        )
