from ..api import app

token = app.config['AMAZON_ACCESS_TOKEN']
secret = app.config['AMAZON_TOKEN_SECRET']

import boto.ec2
conn = boto.ec2.connect_to_region('us-west-2',
                                   aws_access_key_id=token,
                                   aws_secret_access_key=secret)


# inst = conn.run_instance(image_id="ami-f3b320c3",
# security_group_ids=["sg-1dc1dc71",],
# placement="us-west-2a",
# instance_type="cr1.8xlarge",
# subnet_id="subnet-7a7c3612",
# )

# print inst[0]
# instance = inst[0].instances[0]
# print instance
# print instance.id
# print instance.private_ip_address

# instance.add_tag("cloudml", "cloudml")




# req = conn.request_spot_instances(
#     price="1",
#     image_id= "ami-9534a7a5",# "ami-66c8e123",
#     security_group_ids=["sg-1dc1dc71",], #["sg-534f5d3f",],
#     instance_type="m3.xlarge",
#     placement="us-west-2a",
#     subnet_id="subnet-7a7c3612")#"subnet-3f5bc256")

# inst = conn.run_instances(
# image_id='ami-9534a7a5',
# security_group_ids=["sg-1dc1dc71",],
# instance_type="cr1.8xlarge",
# placement="us-west-2a",
# subnet_id="subnet-7a7c3612")

# instance = inst[0].instances[0]
# print instance.private_ip_address
# print instance.state
# print instance.id


# req = conn.get_all_spot_instance_requests(request_ids = [''sir 22e7103e',])
# print req
# req = req[0]
# print req.id
# print req.status
# print req.instance_id
# print req.state

inst = conn.start_instances(instance_ids=['i-49a0597d', ])
print inst
print inst[0].ip_address

#conn.stop_instances(instance_ids=['i-49a0597d'])
# i-07610933 i-fbfcf4cf

# inst = conn.get_all_instances(instance_ids=['i-49a0597d',])#instance_ids=['i-49a0597d', ])
# # instance = inst[0].instances[0]
# # ####instance.terminate()
# image = inst[0].instances[0].create_image('cloudml-worker.v2.7')
# print image

# # # # # #print inst[0], dir(inst[0].instances[0])
# for i in inst:
# #	print i, i.instances[0].id, i.instances[0].private_ip_address
#   	instance = i.instances[0]
# #  	#instance = i
# # # # #instance.add_tag("cloudml", "cloudml")
# # # # # #print instance.stop()
# # 	print instance.private_ip_address
# # 	print instance
# 	#instance.state
# 	instance.terminate()
# image = inst[0].instances[0].create_image('cloudml-worker.v2.2')
# print image
# from api.amazon_utils import AmazonS3Helper
# helper = AmazonS3Helper()
# data = helper.load_key('51bace93106a6c24dd504602')

# import gzip
# import zlib

# ddata = zlib.decompress(data)
# print ddata

# f = gzip.open('./data/51bac787106a6c2165f783f5.gz', 'rb')
# file_content = f.read()
# f.close()

# print file_content


# import cStringIO
# import gzip

# def sendFileGz(bucket, key, fileName, suffix='.gz'):
#     key += suffix
#     mpu = bucket.initiate_multipart_upload(key)
#     stream = cStringIO.StringIO()
#     compressor = gzip.GzipFile(fileobj=stream, mode='w')

#     def uploadPart(partCount=[0]):
#         partCount[0] += 1
#         stream.seek(0)
#         mpu.upload_part_from_file(stream, partCount[0])
#         stream.seek(0)
#         stream.truncate()

#     with file(fileName) as inputFile:
#         while True:  # until EOF
#             chunk = inputFile.read(8192)
#             if not chunk:  # EOF?
#                 compressor.close()
#                 uploadPart()
#                 mpu.complete_upload()
#                 break
#             compressor.write(chunk)
#             if stream.tell() > 10<<20:  # min size for multipart upload is 5242880
#                 uploadPart()