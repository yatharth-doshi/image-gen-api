import boto3
from botocore.exceptions import ClientError
import os
from uuid import uuid4
from fastapi import UploadFile
import io

class S3Helper:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id = os.getenv('API_KEY'),
            aws_secret_access_key = os.getenv('API_SECRET'),
            region_name = os.getenv('AWS_REGION')
        )
        self.bucket_name = os.getenv('BUCKET_NAME')

    def upload_file(self, file: UploadFile, folder: str = "uploads") -> dict:
        """
        Upload a file to S3 and return the URL
        """
        try:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            unique_filename = f"{uuid4()}.{file_extension}"
            s3_key = f"{folder}/{unique_filename}"
            
            # Read file content
            file_content = file.file.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type
            )

            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            return {
                "s3_key": s3_key,
                "url": file_url
            }

            
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")
        finally:
            file.file.close()
    
    # def delete_file(self, file_url: str) -> bool:
    #     """
    #     Delete a file from S3 using its URL
    #     """
    #     try:
    #         # Extract key from URL
    #         key = file_url.replace(f"https://{self.bucket_name}.s3.amazonaws.com/", "")
            
    #         self.s3_client.delete_object(
    #             Bucket=self.bucket_name,
    #             Key=key
    #         )
    #         return True
            
    #     except ClientError as e:
    #         print(f"Failed to delete file from S3: {str(e)}")
    #         return False
    
    # def generate_presigned_url(self, file_url: str, expires_in: int = 3600) -> str:
    #     """
    #     Generate a pre-signed URL for temporary access
    #     """
    #     try:
    #         # Extract key from URL
    #         key = file_url.replace(f"https://{self.bucket_name}.s3.amazonaws.com/", "")
            
    #         url = self.s3_client.generate_presigned_url(
    #             'get_object',
    #             Params={
    #                 'Bucket': self.bucket_name,
    #                 'Key': key
    #             },
    #             ExpiresIn=expires_in
    #         )
    #         return url
            
    #     except ClientError as e:
    #         raise Exception(f"Failed to generate presigned URL: {str(e)}")

# Create global instance
s3_helper = S3Helper()