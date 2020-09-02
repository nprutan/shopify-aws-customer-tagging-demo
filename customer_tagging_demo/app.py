import json
import os

from chalice import Chalice, Response, Cron

from chalicelib.api_clients import (SHOPIFY_API_PATH, get_botocore_client,
                                    get_shopify_client, SHOPIFY_API_CUSTOMER_URI)
from chalicelib.aws_notifications import (create_unknown_customer_msg, 
                                          create_unknown_customers_csv_msg,
                                          send_ses_message, send_sns_notification)
from chalicelib.shopify_customers import (tag_customer_retail, get_all_shopify_customers_recursive,
                                      formatted_customer_info, pass_verification_pipeline as
                                      pass_retail_verification,
                                      email_not_retail, name_not_retail,
                                      spending_not_retail)
from chalicelib.street_lookup import (customer_is_residential, customer_is_unknown,
                                      get_smarty_streets_client)
from chalicelib.customers_csv_writer import (prepare_customer_list, create_untagged_customers_csv,
                                            get_csv_row_count)

app = Chalice(app_name='retail_tagging_v1')
app.debug = True

SHOPIFY_TOKEN = os.environ['SHOPIFY_API_KEY']
SMARTY_ID = os.environ['SMARTY_AUTH_ID']
SMARTY_TOKEN = os.environ['SMARTY_AUTH_TOKEN']
ORDERS_TOPIC = os.environ['SNS_TOPIC_ARN_ORDERS']
CUSTOMER_NEEDS_TAGGING = os.environ['SNS_TOPIC_ARN_CUSTOMER_TAGS']
CUSTOMER_UNKNOWN = os.environ['SNS_TOPIC_ARN_CUSTOMER_UNKNOWN']
SPENDING_THRESHHOLD = int(os.environ['RETAIL_CUSTOMER_SPENDING_THRESHHOLD']) 
S3_BUCKET = os.environ['S3_BUCKET_CUSTOMERS_UNTAGGED']
SES_TO_ADDR = os.environ['SES_TO_ADDRESS']
CRON_SCHEDULE_DAYS = os.environ['CRON_SCHEDULE_DAYS_CUSTOMERS_MESSAGE']
CRON_SCHEDULE_HOURS = os.environ['CRON_SCHEDULE_HOURS_CUSTOMERS_MESSAGE']
sns_client = get_botocore_client('sns')
ses_client = get_botocore_client('ses')
s3_client = get_botocore_client('s3')
shopify_client = get_shopify_client(SHOPIFY_TOKEN)
smarty_client = get_smarty_streets_client(SMARTY_ID, SMARTY_TOKEN)


@app.route('/orders', methods=['POST'])
def orders_endpoint():
    hook_body = app.current_request.json_body
    send_sns_notification(sns_client,  ORDERS_TOPIC, hook_body, serialize=True)
    return Response(body='Thanks red rover!',
                    status_code=200,
                    headers={'Content-Type': 'text/plain'})


@app.on_sns_message(topic= ORDERS_TOPIC)
def verify_customers_residential(event):
    customer = json.loads(event.message)['customer']
    unknown = customer_is_unknown(customer)
    residential = customer_is_residential(client=smarty_client, customer=customer)
    if unknown and residential:
        return send_sns_notification(sns_client,  CUSTOMER_NEEDS_TAGGING, 
                                     customer, serialize=True)
    elif unknown and not residential:
        return send_sns_notification(sns_client,  CUSTOMER_UNKNOWN, 
                                     customer, serialize=True)


@app.on_sns_message(topic= CUSTOMER_NEEDS_TAGGING)
def tag_customer(event):
    customer = json.loads(event.message)
    return tag_customer_retail(shopify_client, customer)


@app.on_sns_message(topic= CUSTOMER_UNKNOWN)
def verify_likely_retail(event):
    customer = json.loads(event.message)
    if pass_retail_verification(funcs_to_apply=[email_not_retail,
                                                name_not_retail, spending_not_retail], 
                                                customer=customer,
                                                spending_threshhold=SPENDING_THRESHHOLD):
        return send_sns_notification(sns_client,  CUSTOMER_NEEDS_TAGGING, 
                                     customer, serialize=True)
    return send_ses_message(ses_client, SES_TO_ADDR, create_unknown_customer_msg, 
                            formatted_customer_info(customer))


@app.schedule(Cron(0, CRON_SCHEDULE_HOURS, '?', '*', CRON_SCHEDULE_DAYS, '*'))
def create_untagged_customers_s3(event):
    customers = get_all_shopify_customers_recursive(shopify_client, SHOPIFY_API_CUSTOMER_URI)
    modified_list = prepare_customer_list(customers)
    orders_csv = create_untagged_customers_csv(modified_list)
    return s3_client.put_object(
        ACL='public-read',
        Body=orders_csv,
        Key='untagged_customers.csv',
        Bucket=S3_BUCKET
    )


@app.on_s3_event(bucket=S3_BUCKET,
                 events=['s3:ObjectCreated:*'])
def create_untagged_customers_msg(event):
    customers_csv = s3_client.get_object(Bucket=event.bucket, Key=event.key)
    row_count = get_csv_row_count(customers_csv)
    msg_info = {'row_count': row_count, 'bucket': event.bucket,
                'key': event.key}
    return send_ses_message(ses_client, SES_TO_ADDR, create_unknown_customers_csv_msg, msg_info)
