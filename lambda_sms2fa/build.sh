#!/bin/bash
if [ -e ../sms2fa.py.zip ] ; then
    rm -f ../sms2fa.py.zip
fi
zip -9r ../sms2fa.py.zip .
cd ..
