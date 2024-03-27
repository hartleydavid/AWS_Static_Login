#Remove sys import if sys.exit is not needed anymore
import sys
import logging
import pymysql
import json
import os

# rds settings
user_name = os.environ['USER_NAME']
db_password = os.environ['PASSWORD']
rds_proxy_host = os.environ['RDS_PROXY_HOST']
db_name = os.environ['DB_NAME']

#Create the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    #Try to connect the the database
    try:
        conn = pymysql.connect(host=rds_proxy_host, user=user_name, passwd=db_password, db=db_name, connect_timeout=5)
    #Log Errors that were thrown during attempted connection
    except pymysql.MySQLError as e:
        logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
        logger.error(e)
        return {
            'statusCode': 500,
            'headers': {
                    'Access-Control-Allow-Origin': 'https://group4staticbucket.s3.us-west-2.amazonaws.com',
            },
            'body': json.dumps({'success': False, 'message': 'Could not connect to MySQL instance. Please try again.'})
        }
        #Is this needed now that connection is inside function?
        #sys.exit(1)
    
    #Log the successful connection to the RDS
    logger.info("SUCCESS: Connection to RDS for MySQL instance succeeded")
    
    # Parse request body
    body = json.loads(event['body'])
    username = body.get('username')
    password = body.get('password')


    #SQL query to insert into db
    query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    
    #Try insert query
    try:
        #With a cursor using the connection to the db
        with conn.cursor() as cur:
            #Execute Insert query
            cur.execute(query, (username, password))
            
            
            #If no error is thrown, account created successfully, commit changes
            conn.commit()
        
        #Return a successful account creation reponse
        return {
            'statusCode': 200,
            'headers': {
            'Access-Control-Allow-Origin': 'https://group4staticbucket.s3.us-west-2.amazonaws.com',
            },
             'body': json.dumps({'success': True, 'message': 'Account Creation Successful'})
        }

    #Error with SQL query execution
    except pymysql.MySQLError as e:
        
        #Log error that is thrown on cloud watch lo
        logger.error("Error executing SQL query: {}".format(e))
        
        #If the error that is caught is the 1062 (duplicate value) error
        if e.args[0] == 1062:
            #Return API response for the duplicate value error
            return {
                'statusCode': 401,
                'headers': {
                        'Access-Control-Allow-Origin': 'https://group4staticbucket.s3.us-west-2.amazonaws.com',
                },
                'body': json.dumps({'success': False, 'message': 'Account Already Exists'})
            }
        
        #Return API response for an SQL error different from the 1062 error
        return {
            'statusCode': 501,
            'headers': {
                    'Access-Control-Allow-Origin': 'https://group4staticbucket.s3.us-west-2.amazonaws.com',
            },
            'body': json.dumps({'success': False, 'message': 'SQL Query Failed.'})
        }
    