import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging
import io
import sys

OPTIONSFILE = 'optionsData.txt'
#OPTIONSFILE = 'optionsDataTest.txt'  #test file
OPTIONSFILETEST = 'optionsDataTest.txt'  #test file
# Retrieve the logger instance
logger = logging.getLogger()

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

HEADER = "   Stock DTE CurrPrice OptsPrice Type Status %OTM Prem"
date_format = "%Y/%m/%d"
today = datetime.today()
logging.debug(today)
isAWS = True

class StockOpt:
    name = ""
    currentPrice = 0
    optsPrice = 0
    optType = ""
    IOTM = ""
    pctIOTM = 0
    expirationDate = ""
    DTE = 0
    premium = 0
    alert = "n"

    def calcPct(self, bid):
        optionsType = self.optType
        optionsPrice = self.optsPrice
        pctIOTM = 0

        if optionsType == "put":
            if optionsPrice < bid:
                IOTM = "OTM"
                pctIOTM = (1 - optionsPrice/bid) * 100
            else:
                IOTM = "ITM"
        else:
            #calls
            if optionsPrice > bid:
                #OTM
                IOTM = "OTM"
                pctIOTM = (optionsPrice/bid - 1) * 100
            else:
                IOTM = "ITM"
                pctIOTM = (bid/optionsPrice - 1) * 100
        return [IOTM, pctIOTM]

    def alerted(self):
        logging.debug("alerted: IOTM: " + self.IOTM + "; pct: " + str(self.pctIOTM))
        alert = "n"
        if self.IOTM == "ITM":
            alert = 'y'

        if self.IOTM == "OTM":
            if self.pctIOTM < 4:
                alert = 'y'

        return alert

    def toString(self):
        logging.debug("stockOptions.toString enter")
        alert = alerted(self)
        if alert == 'y':
            alert = "---"
        else:
            alert = ""

        return "{:3} {:4} {:3} {:>7} {:>7} {:4} {:3} {:>.0f}% {:5}".format(alert, self.name, self.DTE, self.currentPrice, str(self.optsPrice), self.optType, self.IOTM, self.pctIOTM, self.premium)

    def toJson(self):
        logging.debug("stockOptions.toJson enter")

        j = {}
        j['alert'] = self.alerted()
        j['name'] = self.name
        j['DTE'] = self.DTE
        j['price'] = self.currentPrice
        j['optionsPrice'] = self.optsPrice
        j['type'] = self.optType
        j['IOTM'] = self.IOTM
        j['pctIOTM'] = "{:>.0f}%".format(self.pctIOTM)
        j['premium'] = self.premium
        return j

def lambda_handler(event, context):
    logging.debug("lambda_handler enter")
    logger.info('## EVENT')
    logger.info(event)
    requestJson = False
    if 'queryStringParameters' in event and 'requestJson' in event['queryStringParameters']:
        rj = event["queryStringParameters"]["requestJson"]
        if str(rj) == "true":
            #logging.info("setting request for json")
            requestJson = True
    if 'queryStringParameters' in event and 'test' in event['queryStringParameters']:
        OPTIONSFILE = OPTIONSFILETEST
        logging.info("using test options file")

    r = run(requestJson)
    if requestJson:
        return {
            'statusCode': 200,
            'body': json.dumps(r)

            #'statusCode': 200,
            #'body': r
        }

#looks for data-reactid based on agent type
def yScrape2(stock):

    logging.debug("yScrape2 enter")
    url = "https://finance.yahoo.com/quote/" + stock
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup.find_all('span'):
        logging.debug(tag)
        z = re.search(r"data-reactid=\"14\"", str(tag))
        #logging.debug("re: " + str(z))
        if z:
            #logging.debug("z: " + str(z))
            return str(tag)
            break

    logging.debug("no last price found")
    return "---"

#looks for Bid in span then reads price
def yScrape(stock):

    logging.debug("yScrape enter")
    bid = ""
    url = "https://finance.yahoo.com/quote/" + stock
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    isBid = False

    for tag in soup.find_all('span'):
        #logging.debug(tag)
        if isBid:
            bid = str(tag)
            isBid = False
            #that's all we're looking for - now
            logging.debug("Found bid: " + bid)
            break

        z = re.search(r"Bid", str(tag))
        if z:
            isBid = True;

    logging.debug("bid: " + stock + " -- " + bid)
    return bid

def loadOptionsData():

    if isAWS == True:
        import boto3
        s3 = boto3.client('s3')
        try:
            data = s3.get_object(Bucket='larsbucket1', Key=OPTIONSFILE)
            json_data = json.load(data['Body'])
            #json_data = json.load(data['Body'].read())
            return json_data
        except Exception as e:
            logging.critical(e)
            raise e

    else:
        logging.debug("loadOptionsData enter")
        try:
            with open(OPTIONSFILE) as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            print("Error: file not found: " + filename)
            logging.critical("Error: file not found: " + filename)
            exit(1)
        return data

def parseBid2(b):
    #logging.debug("parseBid2: " + b)
    try:
        a = b.split('>')
        #logging.debug("a: " + a)
        b = a[1].split('<')
        #logging.debug("parseBid2: " + str(float(b[0])))
        return float(b[0].replace(",", ""))
    except ValueError:
        logging.warning("Could not convert bid: " + str(b))
        return 9999

def parseBid(b):
    try:
        a = b.split('>')
        b = a[1].split(' ')
        return float(b[0].replace(",", ""))
    except ValueError:
        logging.warning("Could not convert bid: " + str(b))
        return 9999

def run(requestJson):
    #read file into list
    data = loadOptionsData()
    logging.debug(json.dumps(data,indent=4))

    stockOptionsList = []

    for d in data["stock"]:
        stock = d.get("name", "***")
        optionsType = d.get("type", "")
        optionsPrice = float(d.get("price", 9999))
        expDate = d.get("date", "1/1/1970")
        premium = d.get("premium", 0)

        #r = yScrape(stock)
        #bid = parseBid(r)
        r = yScrape2(stock)
        bid = parseBid2(r)

        so = StockOpt()
        so.name = stock
        so.optType = optionsType
        so.currentPrice = bid
        so.optsPrice = optionsPrice
        so.expirationDate = expDate
        so.premium = premium
        a = datetime.strptime(expDate, date_format)
        so.DTE = (a - today).days
        [so.IOTM, so.pctIOTM] = so.calcPct(bid)

        stockOptionsList.append(so)

    #enumerate list

    if requestJson == False:
        logger.info("no json response")
        #report stock, price, options, in/OTM, %OTM, DTE - sort by ITM, DTE
        output = io.StringIO()
        output.write(HEADER + "\n")
    list = []
    #sort by ITM then DTE
    stockOptionsList.sort(key=lambda stockOptions: stockOptions.DTE)
    stockOptionsList.sort(key=lambda stockOptions: stockOptions.IOTM)
    #logging.debug("sorted: " + soSorted)
    for e in stockOptionsList:
        if requestJson:
            list.append(e.toJson())
        else:
            output.write(e.toString() + "\n")

    if requestJson:
        return list
    else:
        return output.getvalue()

if __name__ == '__main__':
    isAWS = False
    requestJson = False
    if len(sys.argv) == 2 :
        if sys.argv[1] == '-json':
            logging.debug("request for json output")
            requestJson = True
    r = run(requestJson)
    if requestJson:
        #logging.debug("r: " + str(len(r)))
        print(json.dumps(r))
    else:
        print(r)
