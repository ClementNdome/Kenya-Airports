from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ComplianceCheck, Notification
from .utils import send_notification_email


@receiver(post_save, sender=ComplianceCheck)
def notify_status_change(sender, instance, created, **kwargs):
    if not created:
        return
    prop = instance.property
    previous = ComplianceCheck.objects.filter(property=prop)\
        .exclude(pk=instance.pk).order_by('-checked_at').first()
    if previous and previous.status != instance.status:
        notification = Notification.objects.create(
            user=prop.user,
            notification_type='status_change',
            title=f'Status changed for {prop.name}',
            message=f'Compliance status changed from {previous.status} to {instance.status}',
            link=f'/my-properties/{prop.pk}/',
        )
        send_notification_email(notification)


@receiver(post_save, sender=Notification)
def email_on_notification(sender, instance, created, **kwargs):
    if created and instance.user.email:
        send_notification_email(instance)
