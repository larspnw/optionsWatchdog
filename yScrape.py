import requests
import urllib.request
import time
import re
import json

from bs4 import BeautifulSoup

url = "https://finance.yahoo.com/quote/AMZN"
#https://finance.yahoo.com/quote/AMZN?p=AMZN&.tsrc=fin-srch-v1
#url = 'https://finance.yahoo.com/quote/AMZN190816C02050000?p=AMZN190816C02050000'
#url = ‘http://web.mta.info/developers/turnstile.html'
response = requests.get(url)

#print(response)

soup = BeautifulSoup(response.text, "html.parser")

isBid = False

for tag in soup.find_all('span'):
    #print(tag)
    if isBid:
        bid = str(tag)
        isBid = False
    z = re.search(r"Bid", str(tag))
    if z:
        isBid = True;

print("bid: " + bid)

exit()
#OLD: looking for the json embedded in the page
#find the script tag
for tag in soup.find_all('script'):
    z = re.search(r"root.App.main", str(tag), re.MULTILINE)
    if z:
        #print(z.string)
        break

#find our data
for line in z.string.splitlines():
    #print(line)
    z = re.search("^root.App.main", line)
    if z:
        #print(z.string)
        break

#get the json
j = z.string.split("root.App.main = ")
#print(j[1])

print(json.dumps(j[1][:-1], indent=4))
data = json.loads(j[1][:-1])
#for d in data["context"]["dispatcher"]["stores"]["StreamDataStore"]:
    #print(d)
    #print(json.dumps(d, indent=2))

#print(data["context"])
#print(data["regularMarketPrice"])
