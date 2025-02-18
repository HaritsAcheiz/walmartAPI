from dataclasses import dataclass
from httpx import Client
from dotenv import load_dotenv
from urllib.parse import urljoin, quote
from base64 import b64encode
from os import getenv
import json
from uuid import uuid4
from time import sleep

load_dotenv()

@dataclass
class WalmartAPI:
    # base_url: str = 'https://api-gateway.walmart.com'
    base_url: str = 'https://marketplace.walmartapis.com'
    client_id: str = ''
    client_secret: str = ''
    access_token: str = ''
    client: Client = Client()

    def get_token(self):
        creds = f"{self.client_id}:{self.client_secret}".encode()
        authorization = b64encode(creds).decode()

        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
        'accept': 'application/json',
        'authorization': f'Basic {authorization}',
        'content-type': 'application/x-www-form-urlencoded',
        'WM_QOS.CORRELATION_ID': uuid4().hex,
        'WM_SVC.NAME': 'Walmart Marketplace'
        }

        payload = "grant_type=client_credentials"

        endpoint = '/v3/token'
        url = urljoin(self.base_url, endpoint)
        self.client = Client(headers=headers)
        response = self.client.post(url, params=payload)
        if response.status_code != 200:
            response.raise_for_status()
        result = response.json()
        self.access_token = result['access_token']


    def handle_response(self, response):
        if response.status_code != 200:
            if response.status_code in [520, 521]:
                print('Internal Server Error...Retry')
                sleep(1)
                return False
            elif response.status_code == 404:
                print('Item not found')
                return True
            elif response.status_code == 401:
                print('Client Error...Get new token')
                self.get_token()
                headers = {
                    'WM_SEC.ACCESS_TOKEN': self.access_token
                }
                self.client.headers.update(headers)
                return False
            else:
                response.raise_for_status()

        return True


    def catalog_search (self, params=None):
        endpoint = f'/v3/items'
        url = urljoin(self.base_url, endpoint)
        headers = {
            'WM_SEC.ACCESS_TOKEN': self.access_token,
        }

        self.client.headers.update(headers)
        breakout = False
        while not breakout:
            response = self.client.get(url, params=params)
            breakout = self.handle_response(response)

        return response.json()


    def delete_item(self, sku):
        sku = quote(sku)
        endpoint = f'/v3/items/{sku}'
        url = urljoin(self.base_url, endpoint)
        headers = {
            'WM_SEC.ACCESS_TOKEN': self.access_token
        }
        self.client.headers.update(headers)
        breakout = False
        while not breakout:
            response = self.client.delete(url)
            breakout = self.handle_response(response)

        return response.json()


    def update_lag_time(self, skus, fulfillment_lag_time, feed_type='lagtime'):
        endpoint = '/v3/feeds'
        url = urljoin(self.base_url, endpoint)

        headers = {
            'WM_SEC.ACCESS_TOKEN': self.access_token
        }

        params = {
            'feedType': feed_type
        }

        self.client.headers.update(headers)
        lag_time = list()
        for sku in skus:
            lag_time.append({"sku": sku, "fulfillmentLagTime": fulfillment_lag_time})

        json_data = {"LagTimeHeader": {"version": "1.0"}, "lagTime": lag_time}
        payload = json.dumps(json_data).encode('utf-8')

        breakout = False
        while not breakout:
            response = self.client.post(url, params=params, data=payload)
            breakout = self.handle_response(response)

        return response.json()


    def get_feed_info(self, feed_id):

        endpoint = f'/v3/feeds/{feed_id}'
        url = urljoin(self.base_url, endpoint)
        headers = {
            'WM_SEC.ACCESS_TOKEN': self.access_token,
        }

        params = {
            'includeDetails': "true"
        }

        self.client.headers.update(headers)
        response = self.client.get(url, params=params)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()


if __name__ == '__main__':
    try:
        api = WalmartAPI(client_id=getenv('WALMART_CLIENT_ID'), client_secret=getenv('WALMART_CLIENT_SECRET'))
        # get access token
        api.get_token()

        # get items
        # params = {
        #     "limit": 50,
        #     "nextCursor": "*",
        #     "lifeCycleStatus": "ACTIVE"
        # }

        # response = api.catalog_search(params=params)
        # print(response)

        # skus = list()
        # for item in response['ItemResponse']:
        #     skus.append(item['sku'])

        # update lag time
        # response = api.update_lag_time(skus, fulfillment_lag_time=3)
        # print(response)

        # get feed info
        response = api.get_feed_info('17E8594D99AB5948AFAFEABD65AC35ED@AVQBCgA')
        print(response)

    except Exception as e:
        print(e)

    finally:
        # client close
        api.client.close()
