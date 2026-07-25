import time
from django.core.management.base import BaseCommand
from investigations.jobs import claim, execute


class Command(BaseCommand):
    help = "Run bounded durable fixture investigations."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            job = claim()
            if job:
                execute(job.id, job.token)
                self.stdout.write(f"Processed job {job.id}")
            if options["once"]:
                return
            time.sleep(1)
