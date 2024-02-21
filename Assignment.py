from flask import Flask, render_template, request, redirect, url_for
import boto3

app = Flask(__name__)

# AWS S3 configurations
#S3_REGION = 'global'
S3_ACCESS_KEY = '***************'
S3_SECRET_KEY = '************************'

s3_client = boto3.client('s3',
                         aws_access_key_id=S3_ACCESS_KEY,
                         aws_secret_access_key=S3_SECRET_KEY)


@app.route('/')
def index():
    buckets = list_buckets()
    return render_template('bucket.html', buckets=buckets)


def list_buckets():
    response = s3_client.list_buckets()
    return [bucket['Name'] for bucket in response['Buckets']]


@app.route('/create_bucket', methods=['POST'])
def create_bucket():
    bucket_name = request.form['bucket_name']
    s3_client.create_bucket(Bucket=bucket_name)
    return redirect(url_for('index'))


@app.route('/delete_bucket', methods=['POST'])
def delete_bucket():
    bucket_name = request.form['bucket_name']
    s3_client.delete_bucket(Bucket=bucket_name)
    return redirect(url_for('index'))


@app.route('/file_manager/<bucket_name>')
def file_manager(bucket_name):
    files = list_files_in_bucket(bucket_name)
    return render_template('file_manager.html', files=files, bucket_name=bucket_name)


def list_files_in_bucket(bucket_name):
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        return [obj['Key'] for obj in response['Contents']]
    else:
        return []


@app.route('/upload_file', methods=['POST'])
def upload_file():
    file = request.files['file']
    file_name = file.filename
    bucket_name = request.form['bucket_name']
    s3_client.upload_fileobj(file, bucket_name, file_name)
    return redirect(url_for('file_manager', bucket_name=bucket_name))


@app.route('/delete_file', methods=['POST'])
def delete_file():
    file_name = request.form['file_name']
    bucket_name = request.form['bucket_name']
    s3_client.delete_object(Bucket=bucket_name, Key=file_name)
    return redirect(url_for('file_manager', bucket_name=bucket_name))


@app.route('/copy_move_file', methods=['POST'])
def copy_move_file():
    source_key = request.form['source_key']
    destination_key = request.form['destination_key']
    bucket_name = request.form['bucket_name']
    s3_client.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': source_key},
                          Key=destination_key)
    return redirect(url_for('file_manager', bucket_name=bucket_name))


if __name__ == '__main__':
    app.run(debug=True)
