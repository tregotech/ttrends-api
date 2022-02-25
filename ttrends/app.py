import json
import pandas as pd
import ast
from ttrends import Trends

def trends_lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    data = event["body"]
    kw_list = ast.literal_eval(data)

    # get trends
    trend = Trends(geo="GB", years=5)
    result = trend.get_trends(kw_list)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": json.loads(result.to_json(orient="table")),
            }
        ),
    }


def related_lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    data = event["body"]
    kw_list = ast.literal_eval(data)

    # get trends
    trend = Trends(geo="GB", years=5)
    result = trend.get_top_related(kw_list)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": json.dumps(result),
            }
        ),
    }


"""
for local testing only
"""



f = open('../events/event.json')
event = json.load(f)
result = trends_lambda_handler(event,None)
print(result['body'])

