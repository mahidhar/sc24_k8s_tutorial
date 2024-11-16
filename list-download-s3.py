import boto3
from botocore import UNSIGNED
from botocore.client import Config
s3 = boto3.client('s3',config=Config(signature_version=UNSIGNED),endpoint_url='https://s3-central.nrp-nautilus.io')
for key in s3.list_objects(Bucket='inet-demo')['Contents']:
    print(key['Key'])

s3.download_file('inet-demo', 'cifar-10-python.tar.gz', 'cifar-10-python.tar.gz')
