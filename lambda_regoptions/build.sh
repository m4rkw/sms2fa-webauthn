#!/bin/bash
if [ -e ../sms2fa_regoptions.py.zip ] ; then
    rm -f ../sms2fa_regoptions.py.zip
fi
zip -9r ../sms2fa_regoptions.py.zip .
cd ..
