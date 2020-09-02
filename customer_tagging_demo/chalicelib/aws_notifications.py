import json

REPLY_TO_ADDR = 'michaelknight@knightindustries.com'
CC_ADDR = 'michaelknight@knightindustries.com'


def send_sns_notification(client, tpc_arn, message_info, serialize=False):
    if serialize:
        message_info = json.dumps(message_info)
    return client.publish(
        TopicArn=tpc_arn,
        Message=message_info,
        MessageStructure='string'
    )


def send_ses_message(client, to_addr, msg_creation_func, msg_info):
    return client.send_email(
        Source='michaelknight@knightindustries.com',
        Destination={
            'ToAddresses': [
                f'{to_addr}',
            ],
            'CcAddresses': [
                CC_ADDR,
            ],
        },
        Message=msg_creation_func(msg_info),
        ReplyToAddresses=[
            REPLY_TO_ADDR,
        ]
    )


def create_unknown_customer_msg(msg_info):
    return {
            'Subject': {
                'Data': f'Please assess untagged customer: {msg_info["email"]}',
            },
            'Body': {
                'Text': {
                    'Data': f'The Customer {msg_info["full_name"]} has an untagged account. \
                            Please assess the account with email: {msg_info["email"]} \
                            Tag customer with appropriate tag.'
                },
                'Html': {
                    'Data': f'<body> \
                            <p>Customer {msg_info["full_name"]} is untagged.</p> \
                            <br/> \
                            <p>Please check account for email: {msg_info["email"]}</p> \
                            <br/> \
                            <p>and update customer account with appropriate tag(s).</p> \
                            <br/> \
                            <p>Link to customer in admin panel:</p>\
                            <p>https://base.myshopify.com/admin/customers/{msg_info["customer_id"]}</p> \
                            </body>'
                }
            }
        }


def create_unknown_customers_csv_msg(msg_info):
    return {
            'Subject': {
                'Data': f'There are still {msg_info["row_count"]} untagged customers that should have their account assessed',
            },
            'Body': {
                'Text': {
                    'Data': f'Please check the CSV file attached and tag customers as necessary.'
                },
                'Html': {
                    'Data': f'<body> \
                            <p>Please check the CSV file attached and tag customers as necessary.</p> \
                            <br/> \
                            <p>Link to customer csv:</p>\
                            <p>https://{msg_info["bucket"]}.s3-us-west-2.amazonaws.com/{msg_info["key"]}</p> \
                            </body>'
                }
            }
        }
