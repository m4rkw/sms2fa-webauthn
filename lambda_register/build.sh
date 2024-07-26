#!/bin/bash
if [ -e ../sms2fa_register.py.zip ] ; then
    rm -f ../sms2fa_register.py.zip
fi
zip -9r ../sms2fa_register.py.zip .
cd ..
