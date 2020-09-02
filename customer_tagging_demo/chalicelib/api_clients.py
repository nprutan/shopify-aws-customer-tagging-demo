import requests
import botocore.session

SHOPIFY_BASE_URI = 'https://base.myshopify.com'

SHOPIFY_API_VERSION = '2020-01'

SHOPIFY_API_PATH = f'{SHOPIFY_BASE_URI}/admin/api/{SHOPIFY_API_VERSION}'

SHOPIFY_API_CUSTOMER_URI = f'{SHOPIFY_API_PATH}/customers/search.json?query=-tag:*&fields:id,email,tags,created_at'


def get_shopify_client(token):
    s = requests.Session()
    s.headers.update({'X-Shopify-Access-Token': f'{token}'})
    return s


def get_botocore_client(service_type, region='us-west-2'):
    session = botocore.session.get_session()
    return session.create_client(service_type, region_name=region)
