#!/bin/bash
./generate_artefact.py sms2fa_authenticate.py.zip lambda_authenticate
./generate_artefact.py sms2fa_authoptions.py.zip lambda_authoptions
./generate_artefact.py sms2fa_register.py.zip lambda_register
./generate_artefact.py sms2fa_regoptions.py.zip lambda_regoptions
./generate_artefact.py sms2fa.py.zip lambda_sms2fa
