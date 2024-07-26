#!/bin/bash
docker build . -t lambda-python312
if [ -e python ] ; then
    rm -rf python
fi
docker run -v ./python:/var/task/python -it lambda-python312 /root/install.sh webauthn
if [ -e webauthn_layer.zip ] ; then
    rm -f webauthn_layer.zip
fi
zip -9r webauthn_layer.zip python/
rm -rf python
docker run -v ./python:/var/task/python -it lambda-python312 /root/install.sh python-pushover2
if [ -e pushover_layer.zip ] ; then
    rm -f pushover_layer.zip
fi
zip -9r pushover_layer.zip python/
rm -rf python
echo
echo "Now push the layers to amazon with:"
echo
echo "aws lambda publish-layer-version --layer-name webauthn-layer-python312 --zip-file fileb://webauthn_layer.zip --compatible-runtimes python3.12"
echo "aws lambda publish-layer-version --layer-name pushover-layer-python312 --zip-file fileb://pushover_layer.zip --compatible-runtimes python3.12"
