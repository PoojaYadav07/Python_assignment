from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# AWS S3 configurations
#S3_REGION = 'global'
# AWS S3 configurations
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client('s3',
                         aws_access_key_id=S3_ACCESS_KEY,
                         aws_secret_access_key=S3_SECRET_KEY)


@app.route('/')
def index():
    buckets = list_buckets()
    error_message = request.args.get('error_message')
    # return render_template('index.html', error_message=error_message)
    return render_template('bucket.html',error_message=error_message, buckets=buckets)


def list_buckets():
    try:
        response = s3_client.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return buckets
    except NoCredentialsError:
        print('AWS credentials not available or incorrect.')
    except Exception as e:
        print(f'Error listing S3 buckets: {e}')
        return []  # Return an empty list in case of an error



    #response = s3_client.list_buckets()
    #return [bucket['Name'] for bucket in response['Buckets']]


@app.route('/create_bucket', methods=['POST'])
def create_bucket():
    bucket_name = request.form['bucket_name']
    try:
        s3_client.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_message = f"Error creating bucket: {e}"
        return redirect(f'/?error_message={error_message}')
    return redirect('/')



@app.route('/delete_bucket', methods=['POST'])
def delete_bucket():
    bucket_name = request.form['bucket_name']
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_message = f"Error deleting bucket: {e}"
        return redirect(f'/?error_message={error_message}')
    return redirect('/')
    # try:
    #     s3_client.delete_bucket(Bucket=bucket_name)
    #     flash(f'Bucket "{bucket_name}" deleted successfully!', 'success')
    # except ClientError as e:
    #     error_code = e.response['Error']['Code']
    #     if error_code == 'BucketNotEmpty':
    #         flash(f'The bucket "{bucket_name}" is not empty. Please delete all objects inside the bucket before attempting to delete it.', 'error')
    #     else:
    #         flash(f'Error deleting bucket "{bucket_name}": {error_code}', 'error')
    # return redirect(url_for('index'))


@app.route('/file_manager/<bucket_name>')
def file_manager(bucket_name):
    files = list_files_in_bucket(bucket_name)
    error_message = request.args.get('error_message')
    return render_template('file_manager.html', files=files, rror_message=error_message, bucket_name=bucket_name)


def list_files_in_bucket(bucket_name):
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        return [obj['Key'] for obj in response['Contents']]
    else:
        return []

@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.form['folder_name']
    bucket_name = request.form['bucket_name']
    try:
        s3_client.put_object(Bucket=bucket_name, Key=(folder_name + '/'))
    except ClientError as e:
        error_message = f"Error creating folder: {e}"
        return redirect(f'/?error_message={error_message}')
    return redirect(url_for('file_manager', bucket_name=bucket_name))

    # return redirect(url_for('file_manager', bucket_name=bucket_name))


@app.route('/upload_file', methods=['POST'])
def upload_file():
    file = request.files['file']
    file_name = file.filename
    bucket_name = request.form['bucket_name']
    try:
        s3_client.upload_fileobj(file, bucket_name, file_name)
    except ClientError as e:
        error_message = f"Error uploading file: {e}"
        return redirect(f'/?error_message={error_message}')
    # return redirect('/')
    return redirect(url_for('file_manager', bucket_name=bucket_name))

@app.route('/delete_folder', methods=['POST'])
def delete_folder():
    folder_name = request.form['folder_name']
    bucket_name = request.form['bucket_name']
    # Deleting all objects with keys that have the specified prefix (folder name)
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
        flash(f'Folder "{folder_name}" deleted successfully from bucket "{bucket_name}"!', 'success')
    except ClientError as e:
        error_code = e.response['Error']['Code']
        flash(f'Error deleting folder "{folder_name}" from bucket "{bucket_name}": {error_code}', 'error')
    return redirect(url_for('file_manager', bucket_name=bucket_name))



@app.route('/delete_file', methods=['POST'])
def delete_file():
    file_name = request.form['file_name']
    bucket_name = request.form['bucket_name']
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=file_name)
    except ClientError as e:
        error_message = f"Error deleting file: {e}"
        return redirect(f'/?error_message={error_message}')
    # return redirect('/')

    return redirect(url_for('file_manager', bucket_name=bucket_name))


@app.route('/copy_move_file', methods=['POST'])
def copy_move_file():
    source_key = request.form['source_key']
    destination_key = request.form['destination_key']
    bucket_name = request.form['bucket_name']
    try:
        s3_client.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': source_key},
                              Key=destination_key)
    except ClientError as e:
        error_message = f"Error copying/moving file: {e}"
        return redirect(f'/?error_message={error_message}')
    # return redirect('/')

    return redirect(url_for('file_manager', bucket_name=bucket_name))


if __name__ == '__main__':
    app.run(debug=True)
