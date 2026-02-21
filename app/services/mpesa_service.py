import requests
import base64
import datetime
from flask import current_app

class MpesaService:
    @staticmethod
    def _sanitize_phone(phone):
        # Remove spaces, dashes, etc.
        phone = str(phone).replace(" ", "").replace("-", "").strip()
        
        # Replace leading +254 or 07 or 01
        if phone.startswith("+254"):
            phone = phone[1:] # remove +
        elif phone.startswith("07") or phone.startswith("01"):
            phone = "254" + phone[1:]
        
        # Check length
        if len(phone) != 12 or not phone.isdigit():
            raise ValueError("Invalid phone number. Must be 12 digits (254...).")
            
        return phone

    @staticmethod
    def get_token():
        consumer_key = current_app.config['MPESA_CONSUMER_KEY']
        consumer_secret = current_app.config['MPESA_CONSUMER_SECRET']
        api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        
        try:
            r = requests.get(api_url, auth=(consumer_key, consumer_secret))
            r.raise_for_status()
            token = r.json().get('access_token')
            return token
        except Exception as e:
            # In production, log this error
            print(f"M-Pesa Token Error: {e}")
            raise e

    @staticmethod
    def initiate_stk_push(phone, amount, reference):
        token = MpesaService.get_token()
        phone = MpesaService._sanitize_phone(phone)
        
        shortcode = current_app.config['MPESA_SHORTCODE']
        passkey = current_app.config['MPESA_PASSKEY']
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        
        password_str = shortcode + passkey + timestamp
        password = base64.b64encode(password_str.encode()).decode()
        
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        
        headers = { "Authorization": f"Bearer {token}" }
        
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": current_app.config['MPESA_CALLBACK_URL'],
            "AccountReference": reference,
            "TransactionDesc": "SAR V2 Premium"
        }
        
        try:
            r = requests.post(api_url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return data.get('CheckoutRequestID')
        except Exception as e:
            print(f"STK Push Error: {e}")
            raise e
