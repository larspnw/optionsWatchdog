import json

data = {}
data['stock'] = []
data['stock'].append({
    'name': 'AMZN',
    'type': 'put',
    'chain': '201908171111'
})
data['stock'].append({
    'name': 'AAPL',
    'type': 'put',
    'chain': '201909171111'
})
data['stock'].append({
    'name': 'GOOG',
    'type': 'put',
    'chain': '201910171111'
})

with open('optionsData.txt', 'w') as outfile:
    json.dump(data, outfile)