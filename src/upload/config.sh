# install dependencies
sudo apt-get update

sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm-6.0-runtime libncurses5-dev \
libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl --fix-missing

# install pyenv
curl https://pyenv.run | bash

# if pyenv not in bash profile
if ! grep -q 'export PATH="$HOME/.pyenv/bin:$PATH' ~/.bash_profile ; then

    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bash_profile
    echo 'eval "$(pyenv init -)"' >> ~/.bash_profile
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bash_profile

    # restart shell
    source ~/.bash_profile
    # exec $SHELL
    echo 'command not exists'

    ./config.sh
else
    pyenv install -v 3.8.6
    pyenv global 3.8.6

    # check version is being successfully set
    pyenv version

    # update pip version
    /home/ubuntu/.pyenv/versions/3.8.6/bin/python3.8 -m pip install --upgrade pip

    # install pipenv
    pip install pipenv

    # install docker for fastapi
    yes | sudo apt install docker.io

    # start docker
    sudo service docker start

    # build image from dockerfile
    sudo docker build -t myimage .

    # run container
    sudo docker run -d --name mycontainer -p 80:80 myimage
fi
