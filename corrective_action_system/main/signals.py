from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.signals import notify
from .models import NonConformity, UserProfile

@receiver(post_save, sender=NonConformity)
def notify_process_owner(sender, instance, created, **kwargs):
    """
    Trigger a notification when a Non-Conformity is created and assigned to a Process Owner.
    """
    if created and instance.assigned_to:
        try:
            # Get the assigned user's UserProfile
            assigned_user_profile = UserProfile.objects.get(user=instance.assigned_to)

            # Ensure the assigned user is a Process Owner
            if assigned_user_profile.role == "Process Owner":
                # Send notification
                notify.send(
                    instance,  # Sender (the Non-Conformity instance)
                    recipient=instance.assigned_to,  # Process Owner
                    verb="New Task Assigned",
                    description=f"You have been assigned a new Non-Conformity: {instance.non_conformity}.",
                    target=instance  # Optional: Add the Non-Conformity as the target
                )
        except UserProfile.DoesNotExist:
            # Handle case where the assigned user has no UserProfile
            pass
