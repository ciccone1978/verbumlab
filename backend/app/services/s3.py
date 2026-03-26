import aioboto3
from core.config import settings
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class S3Service:
    """
    Service for interacting with MinIO/S3 object storage.
    """
    def __init__(self):
        """
        Initialize the S3 service using configuration from app settings.
        """
        self.session = aioboto3.Session()
        self.endpoint_url = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket_name = settings.MINIO_BUCKET_NAME

    async def upload_file(self, file_content: bytes, s3_key: str, content_type: str = "application/pdf"):
        """
        Upload a file to the configured MinIO bucket.

        Args:
            file_content (bytes): The binary content of the file.
            s3_key (str): The destination key in the bucket.
            content_type (str, optional): The MIME type of the file. Defaults to "application/pdf".

        Returns:
            str: The S3 key of the uploaded file.
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as s3:
            try:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=content_type
                )
                logger.info(f"File uploaded to S3: {s3_key}")
                return s3_key
            except ClientError as e:
                logger.error(f"Error uploading to S3: {e}")
                raise

s3_service = S3Service()
