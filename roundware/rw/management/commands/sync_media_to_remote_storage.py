from . import RoundwareCommand
from django.core.files.storage import default_storage
import os
from django.conf import settings

class Command(RoundwareCommand):
    args = ''
    help = 'upload local media directory to the cloud'

    def handle(self, *args, **options):
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for filename in files:
                file_path = os.path.join(root, filename)
                with open(file_path, 'rb') as f:
                    remote_file = default_storage.open(filename, 'wb')
                    remote_file.write(f.read())
                    remote_file.close()

