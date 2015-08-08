# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "hashicorp/precise32"

  #config.vm.provision :shell, path: "bootstrap.sh"

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  config.vm.network :forwarded_port, guest: 3333, host: 3333
  config.vm.network :forwarded_port, guest: 5000, host: 5000

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  # config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
  #   # Customize the amount of memory on the VM:
  #   vb.memory = "1024"
  # end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL  
     sudo bash -c "echo 'deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main' >> /etc/apt/sources.list.d/pgdg.list"
     wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
     sudo apt-get update

     sudo apt-get install -y postgresql-9.4
     sudo -u postgres psql -c "CREATE USER cloudml WITH PASSWORD 'cloudml';"
     sudo -u postgres createdb -O cloudml cloudml

     sudo -u postgres createdb odw
     sudo -u postgres psql -c "ALTER USER Postgres WITH PASSWORD 'postgres'"
     sudo -u postgres psql -d odw -c "CREATE TABLE ja_quick_info (
application bigint,
opening bigint,
employer_info text,
agency_info text,
contractor_info text,
file_provenance character varying(256),
file_provenance_date date
);"
     cp /vagrant/docs/source/_static/dump.tar.gz /tmp/dump.tar.gz
     cd /tmp
     tar -zxvf /tmp/dump.tar.gz
     sudo chmod a+rX ./dump.csv
     sudo -u postgres psql -d odw -c "COPY ja_quick_info FROM '/tmp/dump.csv' CSV HEADER;"

     sudo apt-get install -y build-essential git python-pip python-dev libxml2-dev libxslt1-dev liblapack-dev gfortran libpq-dev libevent-dev rabbitmq-server curl mc

     sudo rabbitmqctl add_user cloudml cloudml
     sudo rabbitmqctl add_vhost cloudml
     sudo rabbitmqctl set_permissions -p cloudml cloudml ".*" ".*" ".*"

     cd /home/vagrant
     export LAPACK=/usr/lib/liblapack.so
     export ATLAS=/usr/lib/libatlas.so
     export BLAS=/usr/lib/libblas.so
     sudo pip install -U numpy==1.7.1
     sudo pip install scipy==0.12.0
     sudo pip install memory-profiler==0.27
     sudo pip install Sphinx==1.3.1
     sudo pip install nose coverage moto==0.3.3 mock==1.0.1
     pip install -r /vagrant/requirements.txt

     # install node
     curl https://raw.githubusercontent.com/creationix/nvm/v0.11.1/install.sh | bash
     source ~/.profile
     nvm ls-remote
     nvm install 0.10.28
     nvm alias default 0.10.28


     sudo npm install -g bower@1.3.9
     sudo npm install -g coffee-script@1.8.0
     sudo npm install -g grunt-cli@0.1.13

     cd /vagrant/ui

     rm -r node_modules bower_components
     npm cache clean
     npm install
     bower cache clean
     bower install

  SHELL
end
