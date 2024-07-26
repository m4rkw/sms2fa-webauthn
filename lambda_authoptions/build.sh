#!/bin/bash
if [ -e ../sms2fa_authoptions.py.zip ] ; then
    rm -f ../sms2fa_authoptions.py.zip
fi
zip -9r ../sms2fa_authoptions.py.zip .
cd ..
