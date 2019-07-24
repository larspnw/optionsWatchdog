import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging

logging.basicConfig(level=logging.WARNING)
#logging.basicConfig(level=logging.DEBUG)
HEADER = "   Stock DTE CurrPrice OptsPrice Type Status %OTM"
date_format = "%Y/%m/%d"
today = datetime.today()
logging.debug(today)

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
        return "{:3} {:4} {:3} {:>7} {:>7} {:4} {:3} {:>.0f}".format(alert, self.name, self.DTE, self.currentPrice, str(self.optsPrice), self.optType, self.IOTM, self.pctIOTM)

def yScrape(stock):

    logging.debug("yScrape enter")
    url = "https://finance.yahoo.com/quote/" + stock
    response = requests.get(url)

    #print(response)

    soup = BeautifulSoup(response.text, "html.parser")

    isBid = False

    for tag in soup.find_all('span'):
        #print(tag)
        if isBid:
            bid = str(tag)
            isBid = False
            #that's all we're looking for - now
            break

        z = re.search(r"Bid", str(tag))
        if z:
            isBid = True;

    logging.debug("bid: " + stock + " -- " + bid)
    return bid

def loadOptionsData():

    logging.debug("loadOptionsData enter")
    filename = "optionsData.txt"
    try:
        with open(filename) as json_file:
            data = json.load(json_file)
            #print(json.dumps(data,indent=4))
    except FileNotFoundError:
        print("Error: file not found: " + filename)
        logging.critical("Error: file not found: " + filename)
    return data

def parseBid(b):
    a = b.split('>')
    b = a[1].split(' ')
    return float(b[0].replace(",", ""))


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
    #print("bid as float: " + bid)
    #print("stock / bid: " + stock + " / " + str(bid))

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
            #print("OTM");
            so.IOTM = "OTM"
            so.pctIOTM = (1 - optionsPrice/bid) * 100
        else:
            so.IOTM = "ITM"
            #print("option is in the money")
    else:
        #calls
        if optionsPrice > bid:
            #OTM
            so.IOTM = "OTM"
            so.pctIOTM = (optionsPrice/bid - 1) * 100
            #print("OTM%:  " + str(OTMpct))
        else:
            so.IOTM = "ITM"
            #print("in the money")
    stockOptionsList.append(so)

#enumerate list

#report stock, price, options, in/OTM, %OTM, DTE - sort by ITM, DTE
print(HEADER)
#sort by ITM then DTE
stockOptionsList.sort(key=lambda stockOptions: stockOptions.DTE)
stockOptionsList.sort(key=lambda stockOptions: stockOptions.IOTM)
#logging.debug("sorted: " + soSorted)
for e in stockOptionsList:
    print(e.toString())

exit(0)


