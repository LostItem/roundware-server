from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = settings.AWS_LOCATION + '/media'
    file_overwrite = False
    default_acl = 'authenticated-read'


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = settings.AWS_LOCATION + '/static'
    default_acl = 'public-read'
