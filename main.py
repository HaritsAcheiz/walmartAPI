from dataclasses import dataclass
from httpx import Client
from dotenv import load_dotenv
from urllib.parse import urljoin
from base64 import b64encode
from os import getenv
import json

load_dotenv()

@dataclass
class WalmartAPI:
    base_url: str = 'https://api-gateway.walmart.com'
    client_id: str = ''
    client_secret: str = ''

    def get_token(self):
        creds = f"{self.client_id}:{self.client_secret}".encode()
        authorization = b64encode(creds).decode()

        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
        'accept': 'application/json',
        'authorization': f'Basic {authorization}',
        'content-type': 'application/x-www-form-urlencoded',
        'WM_QOS.CORRELATION_ID': 'abc1234',
        'WM_SVC.NAME': 'Walmart Marketplace'
        }

        payload = "grant_type=client_credentials"

        url = urljoin(self.base_url, '/v3/token')
        with Client(headers=headers) as client:
            response = client.post(url, params=payload)
        # if response.status_code != 200:
            # response.raise_for_status()
        print(response.content)
        return response



if __name__ == '__main__':
    api = WalmartAPI(client_id=getenv('WALMART_CLIENT_ID'), client_secret=getenv('WALMART_CLIENT_SECRET'))
    token = api.get_token()
    print(token)
