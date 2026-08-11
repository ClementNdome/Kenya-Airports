from django.core.management.base import BaseCommand
from obstacle_compliance.models import Notification


class Command(BaseCommand):
    help = 'Summarize unread notifications (placeholder for email/push integration)'

    def handle(self, *args, **options):
        from django.contrib.auth.models import User
        for user in User.objects.all():
            count = Notification.objects.filter(user=user, is_read=False).count()
            if count:
                self.stdout.write(f'{user.username} has {count} unread notification(s)')
        self.stdout.write(self.style.SUCCESS('Done'))
