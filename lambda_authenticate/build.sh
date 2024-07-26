#!/bin/bash
if [ -e ../sms2fa_authenticate.py.zip ] ; then
    rm -f ../sms2fa_authenticate.py.zip
fi
zip -9r ../sms2fa_authenticate.py.zip .
cd ..
