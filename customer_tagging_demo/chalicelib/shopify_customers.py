from .api_clients import SHOPIFY_API_PATH

SHOPIFY_ADMIN_BASE_URI = 'https://base.myshopify.com/admin'


def _extract_tags(tags):
    return [tag.strip().lower() for tag in tags.split(',')]


def get_customer_group(customer):
    example_categories = ['example1', 'example2', 'example3', 'example4']
    tags = _extract_tags(customer['tags'])
    if 'retail' in tags:
        return 'Retail'
    for tag in tags:
        if tag in example_categories:
            return 'Example'
    return 'Unknown'


def verify_customer_is_unknown(**kwargs):
    customer = kwargs['customer']
    return get_customer_group(customer) == 'Unknown'


def get_customer_id(customer):
    return str(customer['id'])


def _append_tags(tags, new_tag):
    if tags:
        split_tags = tags.split(',')
        split_tags.append(f' {new_tag}')
        return ','.join(split_tags)
    return new_tag


def tag_customer_retail(client, customer):
    customer_id = int(customer['id'])
    updated_tags = _append_tags(customer['tags'], 'retail')
    tag_data = {
        "customer": {
            "id": customer_id,
            "tags": updated_tags
        }
    }
    url = f'{SHOPIFY_API_PATH}/customers/{customer_id}.json'
    return client.put(url, json=tag_data).status_code


def get_shopify_page_link(response):
    link = response.headers.get('link')
    if link:
        for uri in link.split(','):
            if 'next' in uri:
                split = uri.split(';')[0][1:-1]
                if '<' not in split:
                    return split
                return uri.split(';')[0][2:-1]


def get_all_shopify_customers_recursive(client, customer_link, customers=None):
    if not customers:
        customers = []
    response = client.get(customer_link)
    customers.extend(response.json()['customers'])
    customer_link = get_shopify_page_link(response)
    if customer_link:
        get_all_shopify_customers_recursive(client, customer_link, customers)
    return customers


def pass_verification_pipeline(**kwargs):
    for func in kwargs['funcs_to_apply']:
        if not func(**kwargs):
            return False
    return True


def _safe_get_customer_info(order, field):
    if 'customer' in order:
        return order['customer'][field]


def create_admin_link(customer_id):
    return f'{SHOPIFY_ADMIN_BASE_URI}/customers/{customer_id}'


def formatted_customer_info(customer):
    return {'full_name': _safe_get_full_name(customer),
            'customer_id': customer['id'],
            'email': customer['email']}


def _safe_get_full_name(customer):
    if _has_default_address(customer):
        return customer['default_address']['name']
    return f'{customer["first_name"]} {customer["last_name"]}'


def _has_default_address(customer):
    return 'default_address' in customer


def email_not_retail(**kwargs):
    for term in kwargs['flag_terms']:
        if kwargs['customer']['email'] and term in kwargs['customer']['email']:
            return False
    return True


def name_not_retail(**kwargs):
    for term in kwargs['flag_terms']:
        if _has_default_address(kwargs['customer']):
            if term in kwargs['customer']['default_address']['name'].lower():
                return False
    return True
            

def spending_not_retail(**kwargs):
    return float(kwargs['customer']['total_spent']) < kwargs['spending_threshhold']



