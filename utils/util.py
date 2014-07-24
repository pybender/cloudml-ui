token = 'AKIAJ3WMYTNKB77YZ5KQ'
secret = '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'
import boto.ec2
conn = boto.ec2.connect_to_region('us-west-1',
                                   aws_access_key_id=token,
                                   aws_secret_access_key=secret)
print conn.get_all_key_pairs()[-1].copy_to_region('us-west-2')