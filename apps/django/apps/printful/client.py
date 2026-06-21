import requests
from django.conf import settings
from .exceptions import PrintfulError


DEFAULT_BASE_URL = 'https://api.printful.com'


class PrintfulClient:
    def __init__(self, api_token=None, store_id=None, base_url=None):
        self.api_token = api_token or settings.PRINTFUL_API_TOKEN
        self.store_id = store_id or settings.PRINTFUL_STORE_ID
        self.base_url = base_url or settings.PRINTFUL_BASE_URL or DEFAULT_BASE_URL

        if not self.api_token:
            raise PrintfulError('Printful API token is required')

        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.store_id:
            self.headers['X-PF-Store-Id'] = str(self.store_id)

    def _request(self, path, method='GET', body=None):
        url = f'{self.base_url}{path}'
        response = requests.request(
            method,
            url,
            headers=self.headers,
            json=body,
            timeout=30
        )

        try:
            data = response.json()
        except ValueError:
            data = {}

        if not response.ok:
            raise PrintfulError(
                data.get('result') or f'Printful API error {response.status_code}',
                status=response.status_code,
                body=data
            )

        return data

    def get_store_products(self, limit=100, offset=0):
        return self._request(f'/store/products?limit={limit}&offset={offset}')

    def get_store_product(self, product_id):
        return self._request(f'/store/products/{product_id}')

    def get_sync_variant(self, variant_id):
        return self._request(f'/store/variants/{variant_id}')

    def calculate_shipping_rates(self, recipient, items):
        return self._request('/shipping/rates', method='POST', body={'recipient': recipient, 'items': items})

    def create_order(self, payload, confirm=True):
        return self._request(f'/orders?confirm={1 if confirm else 0}', method='POST', body=payload)

    def get_order(self, order_id):
        return self._request(f'/orders/{order_id}')
