try:
    import json
    from pytrends.request import TrendReq
    import time
    import numpy as np
    import pandas as pd
    import tqdm
    import ast
    from scipy import optimize
except Exception as e:
    print("missing modues: {}".format(e))


class Trends:
    def __init__(self, geo="GB", gprop="", cat=0, years=5):
        self.pytrend = TrendReq(hl="en-US", tz=360)
        self.params = {
            "gprop": gprop,
            "geo": geo,
            "timeframe": "today {}-y".format(years),
        }
        self.THRESH = 5  # pytrends api takes max 5 words
        self.SLEEPTIME = 0  # wait 2 seconds between API calls

    def api_call_related(self, kw_list):
        time.sleep(self.SLEEPTIME)
        self.pytrend.build_payload(kw_list, **self.params)
        try:
            related_json = self.pytrend.related_queries()
            df_list = []
            for kw in related_json.keys():
                for cat in ["top", "rising"]:
                    tmp = related_json[kw][cat]
                    tmp["cat"] = cat
                    tmp["kw"] = kw
                    df_list += [tmp]
            result = pd.concat(df_list, axis=0).reset_index(drop=True)
        except:
            result = pd.DataFrame()
        return result

    def api_call_trends(self, kw_list):
        time.sleep(self.SLEEPTIME)
        self.pytrend.build_payload(kw_list, **self.params)
        return self.pytrend.interest_over_time().iloc[:, :-1]

    def get_trends(self, kw_list):
        '''
        main function for getting trends after initialising Trends class
        '''
        if len(kw_list) > 5:
            result = self.chunkwise_trends(kw_list)
            result = self.improve_signal()
        else:
            result = self.api_call_trends(kw_list)
        return result

    def get_top_related(self, kw_list):
        '''
        main function for getting related terms after initialising Trends class
        '''
        df = self.chunkwise_related(kw_list)
        if not sum(df.shape) == 0:
            return sorted(list(set(df.loc[df.cat=='top']['query'])))
        else:
            return []

    def improve_signal(self):
        return self.chunkwise_trends(self.KW_LIST_REORDERED)

    def chunkwise_trends(self, kw_list):
        def rescale_chunks(df_list):
            # calculate factors
            SSE = lambda x, a, b: sum(sum(((a * x) - b) ** 2))
            factors = []
            for i in range(0, len(df_list) - 1):
                section_a, section_b = df_list[i], df_list[i + 1]
                overlap = list(set(section_a.columns).intersection(section_b.columns))
                a, b = section_a[overlap].values, section_b[overlap].values
                x = optimize.minimize(SSE, x0=1, args=(a, b)).x[0]
                factors += [x]
            factors = np.cumsum(factors[::-1])[::-1]  # all factors relative to last one

            # apply factors
            assert len(df_list) == len(factors) + 1

            for idx in range(len(factors)):
                df_list[idx] *= factors[idx]
            result = pd.concat(df_list, axis=1)

            # pivot to avg out duplicates
            rescaled = (
                result.stack()
                .reset_index()
                .pivot_table(index="date", columns="level_1", values=0, aggfunc="mean")
            )
            rescaled.columns.name = None

            rescaled = rescaled[
                rescaled.max().sort_values(ascending=False).index.tolist()
            ]  # order cols by max value
            rescaled = (rescaled / rescaled.values.max() * 100).round(4)  # max == 100

            return rescaled

        STEP = self.THRESH - 2
        df_list = []
        for n in tqdm.tqdm(range(0, len(kw_list), STEP)):
            df_list += [self.api_call_trends(kw_list[n : n + self.THRESH])]
        df_out = rescale_chunks(df_list)
        self.KW_LIST_REORDERED = df_out.columns.tolist()
        return df_out

    def chunkwise_related(self, kw_list):
        STEP = self.THRESH
        df_list = []
        for n in tqdm.tqdm(range(0, len(kw_list), STEP)):
            df_list += [self.api_call_related(kw_list[n : n + self.THRESH])]
        return pd.concat(df_list,axis=0)


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
                # "location": ip.text.replace("\n", "")
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
                # "location": ip.text.replace("\n", "")
            }
        ),
    }


"""
for local testing only

f = open('../events/event.json')
event = json.load(f)
result = lambda_handler(event,None)
print(result['body'])

"""
