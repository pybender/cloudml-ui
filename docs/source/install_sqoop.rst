sudo addgroup hadoop
sudo adduser --ingroup hadoop hduser



wget https://archive.apache.org/dist/hadoop/core/hadoop-1.0.0/hadoop_1.0.0-1_i386.deb
sudo dpkg -i ./hadoop_1.0.0-1_i386.deb
cd cloudml/var/lib
$ sudo tar xzf hadoop-1.0.0.tar.gz
$ sudo mv hadoop-1.0.0 hadoop
$ sudo chown -R hduser:hadoop hadoop