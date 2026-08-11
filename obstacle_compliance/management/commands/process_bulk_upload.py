from django.core.management.base import BaseCommand
from obstacle_compliance.models import BulkUploadJob
from obstacle_compliance.utils import process_bulk_upload


class Command(BaseCommand):
    help = 'Process all pending bulk upload jobs'

    def add_arguments(self, parser):
        parser.add_argument('--job', type=int, help='Process a specific job ID')

    def handle(self, *args, **options):
        if options['job']:
            jobs = BulkUploadJob.objects.filter(pk=options['job'])
        else:
            jobs = BulkUploadJob.objects.filter(status='pending')

        count = jobs.count()
        self.stdout.write(f'Found {count} job(s) to process')

        for job in jobs:
            self.stdout.write(f'Processing job #{job.pk}...')
            try:
                process_bulk_upload(job)
                self.stdout.write(self.style.SUCCESS(f'  Done — {job.success_count}/{job.total_rows} succeeded'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Failed: {e}'))
