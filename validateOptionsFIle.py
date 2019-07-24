import json

try:
    with open('optionsData.txt') as json_file:
        data = json.load(json_file)
        print(json.dumps(data,indent=4))
except FileNotFoundError:
    print("Error: file not found")

#except as err:
    #print("Error validating data: %s", err);

#TODO catch errors and report

    #for p in data['people']:
        #print('Name: ' + p['name'])
        #print('Website: ' + p['website'])
        #print('From: ' + p['from'])
        #print('')