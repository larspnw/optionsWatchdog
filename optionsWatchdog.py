import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging
import io

#TODO: add premium to output
#TODO output as json option

logging.basicConfig(level=logging.WARNING)
#logging.basicConfig(level=logging.DEBUG)
HEADER = "   Stock DTE CurrPrice OptsPrice Type Status %OTM"
date_format = "%Y/%m/%d"
today = datetime.today()
logging.debug(today)
isAWS = True

#Don't need config yet...
#with open('config.json') as json_data_file:
#config = json.load(json_data_file)
#logging.debug("config: " + json.dumps(config, indent=4))
#aws = config["aws"]
#logging.debug("aws: " + aws)

class StockOpt:
    name = ""
    currentPrice = 0
    optsPrice = 0
    optType = ""
    IOTM = ""
    pctIOTM = 0
    expirationDate = ""
    DTE = 0

    def toString(self):
        logging.debug("stockOptions.toString enter")
        alert = ""
        if self.IOTM == "ITM":
            alert = "---"
        return "{:3} {:4} {:3} {:>7} {:>7} {:4} {:3} {:>.0f}%".format(alert, self.name, self.DTE, self.currentPrice, str(self.optsPrice), self.optType, self.IOTM, self.pctIOTM)

def lambda_handler(event, context):

    logging.debug("lambda_handler enter")
    r = run()
    return {
        'statusCode': 200,
        'body': r
    }
    #'body': json.dumps(r)

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
            data = s3.get_object(Bucket='larsbucket1', Key='optionsData.txt')
            json_data = json.load(data['Body'])
            #json_data = json.load(data['Body'].read())
            return json_data
        except Exception as e:
            logging.critical(e)
            raise e

    else:
        logging.debug("loadOptionsData enter")
        filename = "optionsData.txt"
        try:
            with open(filename) as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            print("Error: file not found: " + filename)
            logging.critical("Error: file not found: " + filename)
        return data

def parseBid(b):
    try:
        a = b.split('>')
        b = a[1].split(' ')
        return float(b[0].replace(",", ""))
    except ValueError:
        logging.warning("Could not convert bid: " + str(b))
        return 9999

#TODO - encapsulate and call

def run():
    #read file into list
    data = loadOptionsData()
    logging.debug(json.dumps(data,indent=4))

    stockOptionsList = []

    for d in data["stock"]:
        stock = d["name"]
        optionsType = d["type"]
        optionsPrice = float(d["price"])
        expDate = d["date"]

        r = yScrape(stock)
        bid = parseBid(r)

        so = StockOpt()
        so.name = stock
        so.optType = optionsType
        so.currentPrice = bid
        so.optsPrice = optionsPrice
        so.expirationDate = expDate
        a = datetime.strptime(expDate, date_format)
        so.DTE = (a - today).days

        if optionsType == "put":
            if optionsPrice < bid:
                so.IOTM = "OTM"
                so.pctIOTM = (1 - optionsPrice/bid) * 100
            else:
                so.IOTM = "ITM"
        else:
            #calls
            if optionsPrice > bid:
                #OTM
                so.IOTM = "OTM"
                so.pctIOTM = (optionsPrice/bid - 1) * 100
            else:
                so.IOTM = "ITM"
                so.pctIOTM = (bid/optionsPrice - 1) * 100
        stockOptionsList.append(so)

    #enumerate list

    #report stock, price, options, in/OTM, %OTM, DTE - sort by ITM, DTE
    #TODO print based on output type and runtime
    output = io.StringIO()
    output.write(HEADER + "\n")

    #sort by ITM then DTE
    stockOptionsList.sort(key=lambda stockOptions: stockOptions.DTE)
    stockOptionsList.sort(key=lambda stockOptions: stockOptions.IOTM)
    #logging.debug("sorted: " + soSorted)
    for e in stockOptionsList:
        output.write(e.toString() + "\n")

    return output.getvalue()

if __name__ == '__main__':
    isAWS = False
    r = run()
    print(r)
