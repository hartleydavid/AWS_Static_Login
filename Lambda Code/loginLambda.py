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

#*** Moved connection to rds code to inside the function to allow the lambda 
#*** to update when the RDS changes (new user is created)

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
        
    #Successful SQL connection
    logger.info("SUCCESS: Connection to RDS for MySQL instance succeeded")

    # Parse request body
    body = json.loads(event['body'])
    username = body.get('username')
    password = body.get('password')

    #SQL query
    #Update to be COUNT(*) instead of just *
    #This causes the logic for the rest of the function to not work properly
    #Count will always reutrn a row, current logic works if there is at least
    #one row there is a user, no row = no user
    #Needs to be updated to get the COUNT(*) value such that 0 = invalid login, 
    # 1 = successful login response
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    
    #Try to execute the SQL query
    try:
        with conn.cursor() as cur:
            #Execute query
            cur.execute(query, (username, password))
            #Return all rows
            rows = cur.fetchall()
            
            #If the query gave back rows
            if rows:

                #Return a successful login 
                return {
                    'statusCode': 200,
                    'headers': {
                    'Access-Control-Allow-Origin': 'https://group4staticbucket.s3.us-west-2.amazonaws.com',
                    },
                    'body': json.dumps({'success': True, 'message': 'Login successful'})
                }
            #Not a valid login info
            else:
                return {
                    'statusCode': 401,
                    'headers': {
                    'Access-Control-Allow-Origin': 'https://group4staticbucket.s3.us-west-2.amazonaws.com',
                    },
                    'body': json.dumps({'success': False, 'message': 'Invalid username or password'})
                }
                
    #Error with SQL query
    except pymysql.MySQLError as e:
        
        #Log error on cloud watch
        logger.error("Error executing SQL query: {}".format(e))
        #Return API response for an SQL error
        return {
            'statusCode': 500,
            'headers': {
                    'Access-Control-Allow-Origin': 'https://group4staticbucket.s3.us-west-2.amazonaws.com',
            },
            'body': json.dumps({'success': False, 'message': 'Internal Server Error'})
        }