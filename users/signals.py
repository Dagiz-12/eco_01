from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a profile when a new user is created
    """
    if created:
        Profile.objects.create(user=instance)
        print(f"Profile created for user: {instance.email}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save the profile when the user is saved
    """
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Signal to send welcome email when new user registers
    """
    if created and instance.email:
        try:
            send_mail(
                'Welcome to Hagerbet E-Commerce!',
                f'Hello {instance.username}, welcome to Hagerbet! Your account has been created successfully.',
                settings.DEFAULT_FROM_EMAIL,
                [instance.email],
                fail_silently=True,
            )
            print(f"Welcome email sent to: {instance.email}")
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
