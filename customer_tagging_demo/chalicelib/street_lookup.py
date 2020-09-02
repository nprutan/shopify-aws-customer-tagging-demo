from smartystreets_python_sdk import StaticCredentials, ClientBuilder, exceptions
from smartystreets_python_sdk.us_street import Lookup as StreetLookup
from smartystreets_python_sdk.international_street import Lookup as InternationalLookup
from smartystreets_python_sdk.us_street.match_type import STRICT
from .shopify_customers import get_customer_group

import logging


def get_smarty_client(auth_id, token):
    credentials = StaticCredentials(auth_id, token)
    return ClientBuilder(credentials).build_us_street_api_client()

def _is_domestic_address(addr):
    return addr['country_code'] == 'US'


def _has_default_address(customer):
    return 'default_address' in customer


def _create_lookup(customer):
    address = customer['default_address']
    return StreetLookup(addressee=address['name'], street=address['address1'],
                            street2=address['address2'], city=address['city'],
                            state=address['province'], zipcode=address['zip'],
                            candidates=1, match=STRICT)


def get_lookup_results(client, customer):
    if _has_default_address(customer):
        lookup = _create_lookup(customer)
        try:
            client.send_lookup(lookup)
            return lookup.result
        except exceptions.SmartyException as err:
            logging.debug(err)


def address_rdi_is_residential(result):
    if result:
        return result[0].metadata.rdi == 'Residential'


def customer_is_residential(client=None, customer=None):
    lookup_result = get_lookup_results(client, customer)
    return address_rdi_is_residential(lookup_result)


def customer_is_unknown(customer):
    customer_group = get_customer_group(customer)
    return customer_group == 'Unknown'
