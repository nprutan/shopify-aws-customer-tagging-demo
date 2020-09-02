import csv
import io
from .shopify_customers import (get_customer_group, pass_verification_pipeline,
                            create_admin_link, verify_customer_is_unknown)


def prepare_customer_list(customer_list):
    modified_customer_list = []
    for customer in customer_list:
        customer_id = customer['id']
        if pass_verification_pipeline(funcs_to_apply=[verify_customer_is_unknown], customer=customer):
            modified_customer_list.append({
                'customer_id': customer_id,
                'email': customer['email'],
                'creationdate': customer['created_at'],
                'customergroup': get_customer_group(customer),
                'customer_comments': customer['note'], 'admin_link': create_admin_link(customer_id)
            })
    return modified_customer_list


def _write_customer_rows(writer, customers):
    for customer in customers:
        writer.writerow({'customer_id': customer['customer_id'],
                         'email': customer['email'],
                         'creationdate': customer['creationdate'],
                         'customergroup': customer['customergroup'],
                         'customer_comments': customer['customer_comments'],
                         'admin_link': customer['admin_link']})


_customer_fieldnames_csvwriter = ['customer_id',
                                  'email',
                                  'creationdate',
                                  'customergroup',
                                  'customer_comments',
                                  'admin_link']


def create_untagged_customers_csv(customers):
    f = io.StringIO()
    writer = csv.DictWriter(f, fieldnames=_customer_fieldnames_csvwriter, delimiter=',')
    writer.writeheader()
    _write_customer_rows(writer, customers)
    return f.getvalue()


def get_csv_row_count(s3_object):
    row_count = 0
    for _ in s3_object['Body'].iter_lines():
        row_count += 1
    # minus 1 for header
    return row_count - 1