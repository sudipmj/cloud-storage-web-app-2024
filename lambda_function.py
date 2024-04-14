import json
import mysql.connector
import boto3
import os
import sys
from botocore.exceptions import NoCredentialsError

RDS_HOST = os.environ['RDS_HOST']
RDS_PORT = os.environ['RDS_PORT']
RDS_USER = os.environ['RDS_USER']
RDS_PASSWORD = os.environ['RDS_PASSWORD']
RDS_DB_NAME = os.environ['RDS_DB_NAME']

AWS_BUCKET_NAME = os.environ['AWS_BUCKET_NAME']
AWS_S3_REGION = os.environ['AWS_S3_REGION']

def lambda_handler(event, context):
    user_email = event.get('email')
    user_pass = event.get('pass')
    file_name = event.get('filename')
    
    # Connect to the MySQL database
    db = mysql.connector.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        user=RDS_USER,
        password=RDS_PASSWORD,
        database=RDS_DB_NAME
    )
    
    # Create a cursor object
    cursor = db.cursor()

    try:
        # Execute a query to check if the email and password match
        auth_qry = "SELECT u.sid FROM t_sec_user u WHERE u.user_email = %s AND u.user_password = %s"
        cursor.execute(auth_qry, (user_email, user_pass))

        # Fetch the sid
        sid = cursor.fetchone()

        # If a matching user is found, return True
        if sid is None:
            cursor.close()
            return {
                'statusCode': 401,
                'body': json.dumps('Authentication failed. Invalid email or password.')
            }
        else:
            # Get key value from
            # Generate a presigned URL for the S3 object
            presigned_url = generate_presigned_url(sid, file_name)
            cursor.close()
            return {
                'statusCode': 200,
                'body': json.dumps({'Result': presigned_url})
            }

    except Exception as e:
        # print(f"Error during authentication: {str(e)}")
        return {
            'statusCode': 401,
            'body': json.dumps(f"Error during authentication: {str(e)}")
        }

def generate_presigned_url(sid, file_name):
    s3_obj_key = str(sid) + '/' + str(file_name)

    # Specify the expiration time for the presigned URL (in seconds)
    expiration_time = 6000  # 1hr

    # Create an S3 client
    s3_client = boto3.client('s3')

    # Generate a presigned URL for the S3 object
    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': AWS_BUCKET_NAME,
                'Key': s3_obj_key
            },
            ExpiresIn=expiration_time
        )
        return presigned_url
    except NoCredentialsError as e:
        return str(e)
