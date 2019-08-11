import logging
import json

INCOMINGFILE = 'optionsIn.txt'
#OPTIONSFILE = 'optionsData.txt'
OPTIONSFILE = 'optionsDataTest.txt'  #test file
# Retrieve the logger instance
logger = logging.getLogger()
#logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    logger.debug("event: " + json.dumps(event))
    body = event["body"]
    logger.debug("body: " + json.dumps(body))
    isAWS = True

    r = run()


    #TODO write new options data file
    return {
        'body': json.dumps('Status: ' + body)
        #TODO return status
    }

def run(reqBody):
    data = loadOptionsData()
    if isAWS:
        inData = reqBody
    else:
        inData = loadOptionsIn()

    for stock in inData:
        logging.debug("stock" + json.dumps( stock))
        data["stock"].append(stock)

    logging.debug("end data:")
    logging.debug(json.dumps(data))
    return data

def writeOptionsData():

HERE - getting heavy - look into S3 put_object

        import boto3
        s3 = boto3.client('s3')
        try:
            data = s3.get_object(Bucket='larsbucket1', Key=OPTIONSFILETMP)
            json_data = json.load(data['Body'])
            #json_data = json.load(data['Body'].read())
            return json_data
        except Exception as e:
            logging.critical(e)
            raise e

def loadOptionsIn():
    logging.debug("loadOptionsIn enter")
    try:
        with open(INCOMINGFILE) as json_file:
        data = json.load(json_file)
    except FileNotFoundError:
        print("Error: file not found: " + INCOMINGFILE)
        logging.critical("Error: file not found: " + INCOMINGFILE)
        exit(1)

    return data

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

if __name__ == '__main__':
    isAWS = False
    r = run()
    print(json.dumps(r))
