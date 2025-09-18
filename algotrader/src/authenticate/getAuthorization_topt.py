import json
import requests
import pyotp
from urllib import parse
from fyers_apiv3 import fyersModel
from urllib.parse import urlparse, parse_qs
import apicalls.credentials as cr
import time as tm
import sys

SUCCESS = 1
ERROR = -1

file_path = r"C:\Users\Gautam\myproject\myalgo\algotrader\src\authenticate\files/access_token.txt"

APP_ID = cr.APP_ID
APP_TYPE = cr.APP_TYPE
SECRET_KEY = cr.SECRET_KEY
client_id = "{}-{}".format(APP_ID, APP_TYPE)

FY_ID=cr.FY_ID
APP_ID_TYPE=cr.APP_ID_TYPE

TOTP_KEY=cr.TOTP_KEY
PIN=cr.PIN
REDIRECT_URI=cr.REDIRECT_URI

# API endpoints
BASE_URL = "https://api-t2.fyers.in/vagator/v2"
BASE_URL_2 = "https://api-t1.fyers.in/api/v3"
URL_SEND_LOGIN_OTP = BASE_URL + "/send_login_otp"
URL_VERIFY_TOTP = BASE_URL + "/verify_otp"
URL_VERIFY_PIN = BASE_URL + "/verify_pin"
# URL_TOKEN = BASE_URL_2 + "/token"
URL_TOKEN = "https://api-t1.fyers.in/api/v3/token"
URL_VALIDATE_AUTH_CODE = BASE_URL_2 + "/validate-authcode"

def send_login_otp(fy_id, app_id):
    try:
        result_string1 = requests.post(url=URL_SEND_LOGIN_OTP, json={
            "fy_id": fy_id, "app_id": app_id})
        if result_string1.status_code != 200:
            return ['ERROR', result_string1.text]
        result = json.loads(result_string1.text)
        request_key = result["request_key"]
        return ['SUCCESS', request_key]
    except Exception as e:
        return ['ERROR', e]


def generate_totp(secret):
    try:
        generated_totp = pyotp.TOTP(secret).now()
        return ['SUCCESS', generated_totp]

    except Exception as e:
        return ['ERROR', e]


def verify_totp(request_key, totp):
    print("6 digits verify_totp>>>",totp)
    print("request key>>>",request_key)
    try:
        result_string2 = requests.post(url=URL_VERIFY_TOTP, json={
            "request_key": request_key, "otp": totp})
        if result_string2.status_code != 200:
            return ['ERROR', result_string2.text]
        result = json.loads(result_string2.text)
        request_key = result["request_key"]
        return ['SUCCESS', request_key]
    except Exception as e:
        return ['ERROR', e]

def verify_PIN(request_key, pin):
    try:
        payload = {
            "request_key": request_key,
            "identity_type": "pin",
            "identifier": pin
        }

        result_string3 = requests.post(url=URL_VERIFY_PIN, json=payload)
        if result_string3.status_code != 200:
            return ['ERROR', result_string3.text]
        result = json.loads(result_string3.text)
        access_token = result["data"]["access_token"]
        return ['SUCCESS', access_token]
    except Exception as e:
        return ['ERROR', e]

def token(fy_id, app_id, redirect_uri, app_type, access_token):
    try:
        payload = {
            "fyers_id": fy_id,
            "app_id": app_id,
            "redirect_uri": redirect_uri,
            "appType": app_type,
            "code_challenge": "",
            "state": "sample_state",
            "scope": "",
            "nonce": "",
            "response_type": "code",
            "create_cookie": True
        }
        headers = {'Authorization': 'Bearer {}'.format(access_token)}

        result_string = requests.post(
            url=URL_TOKEN, json=payload, headers=headers
        )
        print("result_string>>",result_string.text)
        if result_string.status_code != 308:
            return [ERROR, result_string.text]

        result = json.loads(result_string.text)
        print("1>>>>",result)
        url = result["Url"]
        
        auth_code = parse.parse_qs(parse.urlparse(url).query)['auth_code'][0]

        return [SUCCESS, auth_code]
    
    except Exception as e:
        return [ERROR, e]
    


def main_login():

    # Step 1 - Retrieve request_key from send_login_otp API

    session = fyersModel.SessionModel(client_id=client_id, secret_key=SECRET_KEY, redirect_uri=REDIRECT_URI,response_type='code', grant_type='authorization_code')

    urlToActivate = session.generate_authcode()
    print('URL to activate APP:  {}'.format(urlToActivate))

    send_otp_result = send_login_otp(fy_id=FY_ID, app_id=APP_ID_TYPE)
    print(send_otp_result)
    if send_otp_result[0] != 'SUCCESS':
        print("send_login_otp msg failure - {}".format(send_otp_result[1]))
        status=False
        sys.exit()
    else:
        print("Step 1 : Step 1 - Retrieve request_key from send_login_otp API 'SUCCESS'")
        status=False

    # Step 2 - Generate totp
    generate_totp_result = generate_totp(secret=TOTP_KEY)
    if generate_totp_result[0] != 'SUCCESS':
        print("generate_totp msg failure - {}".format(generate_totp_result[1]))
        sys.exit()
    else:
        print("Step 2 Generate_totp msg 'SUCCESS'")

    # Step 3 - Verify totp and get request key from verify_otp API
    for i in range(1, 3):

        request_key = send_otp_result[1]
        totp = generate_totp_result[1]
        print("otp>>>",totp)
        verify_totp_result = verify_totp(request_key=request_key, totp=totp)
        print("r==",verify_totp_result)

        if verify_totp_result[0] != 'SUCCESS':
            print("verify_totp_result msg failure - {}".format(verify_totp_result[1]))
            status=False

            tm.sleep(1)
        else:
            print("Step 3 - Verify totp and get request key from verify_otp API SUCCESS")
            status=False
            break

    if verify_totp_result[0] =='SUCCESS':

        request_key_2 = verify_totp_result[1]

        # Step 4 - Verify pin and send back access token
        ses = requests.Session()
        verify_pin_result = verify_PIN(request_key=request_key_2, pin=PIN)
        if verify_pin_result[0] != 'SUCCESS':
            print("verify_pin_result got failure - {}".format(verify_pin_result[1]))
            sys.exit()
        else:
            print("Step 4 - Verify pin and send back access token SUCCESS")


        ses.headers.update({
            'authorization': "Bearer {}".format(verify_pin_result[1])
        })

# Step 5 - Get auth code for API V2 App from trade access token
        print("verify_pin_result[1]>>>",verify_pin_result[1])
        token_result = token(
        fy_id=FY_ID, app_id=APP_ID, redirect_uri=REDIRECT_URI, app_type=APP_TYPE,
        access_token=verify_pin_result[1])
        print("token_result[0]>>>>",token_result[0])
        if token_result[0] != 1:
            print("token_result msg failure - {}".format(token_result[1]))
            sys.exit()
        else:
            print("Step 5 - Get auth code for API V2 App from trade access token SUCCESS")

    # Step 6 - Get API V2 access token from validating auth code
        auth_code = token_result[1]
        session.set_token(auth_code)
        response = session.generate_token()
        if response['s'] =='ERROR':
            print("\n Cannot Login. Check your credentials thoroughly!")
            status=False
            tm.sleep(10)
            sys.exit()

        accesstoken = response["access_token"]
        with open(file_path, 'w') as file:
    # Write the string to the file
            file.write(accesstoken)
        print("Step 6 - Get API V2 access token from validating auth code Final One SUCCESS ",accesstoken)
    return True

def check_valid_fyerID():
    file_path = r"C:\Users\Gautam\eclipse-workspace\MyTradingApp\src/files/access_token.txt"
    appId = "U3H3EN1CN7-100"
    log_path = r"C:\Users\Gautam\eclipse-workspace\MyTradingApp\logs"
    with open(file_path, 'r') as file:
        # Read and print the entire content of the file
        access_token = file.read()
    is_async = False
    fyers = fyersModel.FyersModel(token=access_token, is_async=is_async, log_path=log_path, client_id=appId)
    profile_data = fyers.get_profile()
    profile_data["data"].update({"access_token": access_token,
                         "appId":appId})
    if profile_data.get("s") == "ok":
        fy_id = profile_data["data"]["fy_id"]
        if fy_id == "DS03367":
            return profile_data
        else:
            return False
    else:
        return False
    

if __name__ == "__main__":
    if check_valid_fyerID() == False:
        main_login()
        print(" You now have a new token")
        check_valid_fyerID()
    else:
        print(" You have a valid token")
        check_valid_fyerID()




