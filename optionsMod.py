import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    logger.debug("event: " + json.dumps(event))
    body = None
    if 'body' in event:
        body = event["body"]
    if body is None:
        return {
            'statusCode': 500,
            'body': json.dumps('Input json not received')
        }

    logger.debug("body: " + json.dumps(body))
    stocks = {}
    try:
        stocks = json.loads(body)
        #logger.debug("loaded: ",  stocks)

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('could not load json body')
        }

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    table = dynamodb.Table('Options')
    for stock in stocks:
        logging.debug("stock: ", stock)

        name = stock.get("name", "unknown")
        optionsType = stock.get("type", "")
        optionsPrice = stock.get("price", 9999)
        expirationDate = stock.get("date", 1/1/1970)
        premium = stock.get("premium", "0")

        table.put_item(
            Item={
                'nameTypePrice': name + optionsType + optionsPrice,
                'name': name,
                'type': optionsType,
                'optionsPrice': optionsPrice,
                'expirationDate': expirationDate,
                'premium': premium,
            }
        )
    return {
        'statusCode': 200,
        'body': json.dumps('success'),
    }
