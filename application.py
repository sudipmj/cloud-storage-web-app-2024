from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import NoCredentialsError

application = Flask(__name__)
application.secret_key = 'insert_secret_key_here'  # Change this to a secret key for session management

from config import (
    RDS_HOST, RDS_PORT, RDS_USER, RDS_PASSWORD, RDS_DB_NAME,
    AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_BUCKET_NAME, AWS_REGION, AWS_S3_REGION, AWS_DLQ_URL
)

# Create a connection to RDS
db = mysql.connector.connect(
    host=RDS_HOST,
    port=RDS_PORT,
    user=RDS_USER,
    password=RDS_PASSWORD,
    database=RDS_DB_NAME
)

cursor = db.cursor()

# Routes
@application.route('/')
def home():
    if 'sid' in session:
        # Fetch user details to display on the home page
        cursor.execute('SELECT * FROM t_sec_user t WHERE t.sid= %s', (session['sid'],))
        user_details = cursor.fetchall()
        user_sid = user_details[0][1]
        # check no of uploaded files
        cursor.execute('SELECT COUNT(*) FROM t_drive_cont d WHERE d.dir_id= %s',(user_sid,))
        total_files = cursor.fetchone()[0]

        if total_files != 0:
            # Fetch uploaded files from S3
            try:
                s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_S3_REGION)
                
                s3_objects = s3.list_objects(Bucket=AWS_BUCKET_NAME, Prefix=f'{user_sid}/')['Contents']

                uploaded_files = [{
                    'f_name': obj['Key'].split('/')[-1],
                    'f_type': obj['Key'].split('.')[-1],  # assuming the file type is the extension
                    'f_size': obj['Size'],
                    'f_size_mb': round(obj['Size'] / (1024 * 1024), 2),
                    'f_uploaded_on': obj['LastModified'].strftime('%b %d, %Y, %H:%M:%S'),
                    'presigned_url': generate_presigned_url(s3, AWS_BUCKET_NAME, obj['Key'])
                } for obj in s3_objects]

            except NoCredentialsError:
                flash('AWS credentials not available', 'error')
                uploaded_files = []

            except Exception as e:
                flash(f'Error fetching S3 objects: {str(e)}', 'error')
                uploaded_files = []

            return render_template('drive/home.html', user_details=user_details, uploaded_files=uploaded_files, total_files=total_files)

        # Print debug information

        return render_template('drive/home.html', user_details=user_details, total_files=total_files)

    else:
        return render_template('index.html')


def generate_presigned_url(s3_client, bucket_name, object_key, expiration=360):
    """
    Generate a presigned URL for an S3 object.
    :param s3_client: Boto3 S3 client
    :param bucket_name: S3 bucket name
    :param object_key: Key of the S3 object
    :param expiration: Expiration time for the URL in seconds (6mins)
    :return: Presigned URL
    """
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': object_key},
        ExpiresIn=expiration,
    )
    return url


@application.route('/delete_file', methods=['POST'])
def delete_file():
    if 'sid' in session:
        user_sid = session['sid']
        file_key = request.form['file_key']
        
        # Extract file name from the file key
        file_name = file_key.split('/')[-1]

        try:
            s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)

            # Delete the S3 object
            s3.delete_object(Bucket=AWS_BUCKET_NAME, Key=file_key)

            # Update database
            cursor.execute('DELETE FROM t_drive_cont t WHERE t.dir_id = %s AND t.f_name = %s',(user_sid,file_name))
            db.commit()

            flash('File successfully deleted from S3', 'success')

        except NoCredentialsError:
            flash('AWS credentials not available', 'error')

        except Exception as e:
            flash(f'Error deleting S3 object: {str(e)}', 'error')

    return redirect(url_for('home'))

@application.route('/signup', methods=['POST'])
def signup():
    user_email = request.form['f_signup_email']
    user_name = request.form['f_signup_name']
    user_pass = request.form['f_signup_pass']
    user_conf_pass = request.form['f_signup_conf_pass']

    # Check if passwords match
    if user_pass != user_conf_pass:
        flash('Passwords dont match Please retype passwords.', 'error')
        return redirect(url_for('home'))

    # Check if the username is already taken
    cursor.execute('SELECT * FROM t_sec_user t WHERE t.user_email = %s', (user_email,))
    existing_user = cursor.fetchone()

    if existing_user:
        flash('Username already taken. Please choose another.', 'error')
        return redirect(url_for('home'))

    # Generate Unique SID for new user
    sid_gen = abs(hash(user_email))

    # Set Folder Path for user inside S3 Bucket
    dir_path = 's3://cloud-sa2024-drive/' + str(sid_gen) + '/'

    # Insert the new user into the database
    cursor.execute('INSERT INTO t_sec_user (user_email, sid, user_fname, user_password, user_created_on) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP())', (user_email, sid_gen, user_name, user_pass))
    db.commit()

    # Get the SID of the newly inserted user
    cursor.execute('SELECT sid FROM t_sec_user t WHERE t.user_email = %s', (user_email,))
    sid = cursor.fetchone()[0]

    # Insert user details into the user_details table
    cursor.execute('INSERT INTO t_drive_dtl (sid, dir_id, dir_path, dir_size, dir_created_on) VALUES (%s, %s, %s, 0, CURRENT_TIMESTAMP())', (sid_gen, sid_gen, dir_path))
    db.commit()

    session['sid'] = sid
    return redirect(url_for('home'))


@application.route('/login', methods=['POST'])
def login():
    signin_email = request.form['signin_email']
    signin_pass = request.form['signin_pass']

    # Check if the username and password match a user in the database
    cursor.execute('SELECT * FROM t_sec_user WHERE user_email = %s AND user_password = %s', (signin_email, signin_pass))
    user = cursor.fetchone()

    if user:
        session['sid'] = user[1]
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password. Please try again.', 'error')
        return redirect(url_for('home'))


@application.route('/logout', methods=['POST'])
def logout():
    session.pop('sid', None)
    return redirect(url_for('home'))


@application.route('/uploadtos3', methods=['POST'])
def upload_file():
    if 'sid' in session:
        # Fetch user details to construct S3 key
        cursor.execute('SELECT * FROM t_sec_user t WHERE t.sid= %s', (session['sid'],))
        user_sid = cursor.fetchone()[1]

        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('home'))

        file = request.files['file']


        # If the user does not select a file, browser also submits an empty part without a filename
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('home'))

        # If filesize is greater than 5MB then abort
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
        if file.content_length > MAX_FILE_SIZE:
            flash('File size exceeds the limit (5MB)', 'error')
            return redirect(url_for('home'))

        try:
            # Get additional file details from hidden inputs
            filename = str(request.form.get('filename'))
            filesize = str(request.form.get('filesize'))
            fileextension = str(request.form.get('fileextension'))
            gen_f_id = abs(hash(str(user_sid) + filename + filesize))

            # Upload file to S3
            s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)
            s3_key = f'{user_sid}/{file.filename}'  # Adjust the key as per requirement
            s3.upload_fileobj(file, AWS_BUCKET_NAME, s3_key)

            # If the upload to S3 is successful, insert file details into t_drive_cont table
            cursor.execute('INSERT INTO t_drive_cont (dir_id, f_id, f_name, f_type, f_size, f_uploaded_on) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP())', (user_sid, gen_f_id, filename, fileextension, filesize))
            db.commit()

            # Update directory size in t_drive_dtl table
            cursor.execute('SELECT dir_size FROM t_drive_dtl dd WHERE dd.dir_id = %s',(user_sid,))
            size_to_add = int(cursor.fetchone()[0]) + int(filesize)
            cursor.execute('UPDATE t_drive_dtl dd SET dir_size = %s WHERE dd.dir_id = %s',(size_to_add, user_sid))
            db.commit()

            flash('File successfully uploaded to S3', 'success')

        except NoCredentialsError:
            flash('AWS credentials not available', 'error')
        
        except Exception as e:
            send_message_to_dlq(s3_key)
            flash(f'Error: {str(e)}', 'error')

        return redirect(url_for('home'))

    else:
        return render_template('index.html')

def send_message_to_dlq(s3_key):
    sqs = boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)
    queue_url = AWS_DLQ_URL
    
    try:
        # Send message to DLQ
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=f'Failed to upload file: {s3_key}'
        )
        # flash(f'File upload failed. Sending message to DLQ: {str(e)}')

    except Exception as e:
        # Handle errors while sending message to DLQ
        flash(f'Failed file upload. Failed sending message to DLQ: {str(e)}')

if __name__ == '__main__':
    application.run(debug=True)