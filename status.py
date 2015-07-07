#!/usr/bin/env python
#-*- coding: UTF-8 -*-

# autor: Carlos Rueda
# date: 2015-03-25
# mail: carlos.rueda@deimos-space.com
# version: 1.0

##################################################################################
# version 1.0 release notes:
# Initial version
# Requisites: 
#	library configobj 			To install: "apt-get install python-configobj"
#   library boto (amazonS3)		To install: "pip install boto"
#   library tinyS3 (amazonS3)	To install: "pip install tinys3"
#   library mandrill 			To install: "pip install mandrill"
#   library urllib2 			To install: "pip install urllib2"
##################################################################################

import time
import sys
import os
import datetime
import logging, logging.handlers
import sqlalchemy
import uuid
import httplib
import urllib2
#import urllib
import locale
import pytz

import tinys3
import mandrill
import chilkat

#### VARIABLES #########################################################
from configobj import ConfigObj
config = ConfigObj('./status.properties')

INTERNAL_LOG_FILE = config['directory_logs'] + "/status.log"
LOG_FOR_ROTATE = 10

GRAPHS_FOLDER = config['directory_graphs']

S3_ENDPOINT = config['s3_endpoint']
S3_ACCESS_KEY = config['s3_keyId']
S3_SECRET_KEY = config['s3_secretKey']
S3_BUCKET = config['s3_bucket']
S3_TEST_FILE_NAME = config['s3_test_file_name']
S3_TEST_FILE_COMPLETE_NAME = config['s3_test_file_complete_name']

MANDRILL_API_KEY = config['mandrill_key']
MANDRILL_FROM_EMAIL = config['test_from_email'] 
MANDRILL_FROM_NAME = config['test_from_name']
MANDRILL_TEMPLATE_NAME = config['test_template_name']
MANDRILL_SUBJECT = config['test_subject']

########################################################################

#### LOGGER #########################################################
try:
	logger = logging.getLogger('sdhercules-status')
	loggerHandler = logging.handlers.TimedRotatingFileHandler(INTERNAL_LOG_FILE, 'midnight', 1, backupCount=LOG_FOR_ROTATE)
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	loggerHandler.setFormatter(formatter)
	logger.addHandler(loggerHandler)
	logger.setLevel(logging.DEBUG)
except:
	print '------------------------------------------------------------------'
	print '[ERROR] Error writing log at %s' % INTERNAL_LOG_FILE
	print '[ERROR] Please verify path folder exits and write permissions'
	print '------------------------------------------------------------------'
	exit()
########################################################################

########################################################################
# Funciones auxiliares
#
########################################################################

def test_s3():
	try:
		f = open(S3_TEST_FILE_COMPLETE_NAME,'rb') 

	    # Conectar con S3
		conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,tls=True, endpoint=S3_ENDPOINT)
		logger.debug ("Conectado con S3")
		
		# Subir el fichero a S3
		conn.upload(S3_TEST_FILE_NAME,f,S3_BUCKET,public=True)
		logger.debug ("Fichero subido a S3")
		
		# Construir la url
		s3_url_graph = "https://" + S3_ENDPOINT + "/" + S3_BUCKET + "/" + S3_TEST_FILE_NAME
		logger.debug ("URL del grafico en S3: " + s3_url_graph)

		# Comprobar 
		req = urllib2.Request(s3_url_graph)
		urllib2.urlopen(req)

		# Borrar el fichero subido
		conn.delete(S3_TEST_FILE_NAME,S3_BUCKET)

		return "OK"

	except urllib2.HTTPError, e:
		logger.error('HTTPError = ' + str(e.code))
	except urllib2.URLError, e:
		logger.error('URLError = ' + str(e.reason))
	except httplib.HTTPException, e:
		logger.error('HTTPException')
	except IOError as e:
		logger.error ("Error al acceder al fichero: error({0}): {1}".format(e.errno, e.strerror))
	except Exception:
		import traceback
		logger.error('generic exception: ' + traceback.format_exc())
    	
	return "NOK"


def test_mandril():
	global_merge_vars_array = []
	to_array = []
	merge_vars_array = []
	to_array.append({'email': 'crueda@gmail.com'})
	message = {'from_email': MANDRILL_FROM_EMAIL, 'from_name': MANDRILL_FROM_NAME,
		'to': to_array,
        'merge_vars': merge_vars_array, 'global_merge_vars': global_merge_vars_array,
        'subject': 'test'}
	send_at_date = datetime.datetime.now()
	if send_at_date < datetime.datetime.now():
		send_at_date = send_at_date + datetime.timedelta(days=0)
	local_tz = pytz.timezone('Europe/Madrid')
	send_at_date = local_tz.localize(send_at_date, is_dst=None)
	send_at_date = send_at_date.astimezone(pytz.utc)
	response = send_mail_with_mandrill(MANDRILL_TEMPLATE_NAME, [], message, send_at_date)
	for r in response:
		try:
			if (r['status']=='sent'):
				return "OK"
			else:
				return "NOK"

		except Exception as e:
			raise e
			return "NOK"

	return "OK"


def send_mail_with_mandrill(template_name, template_content, message, send_at):
	mandrill_client = mandrill.Mandrill(MANDRILL_API_KEY)
	try:
		response = mandrill_client.messages.send_template(template_name=template_name,
                                                          template_content=template_content,
                                                          message=message,
                                                          send_at=send_at.strftime("%Y-%m-%d %H:%M:%S"))
		return response
	except Exception as e:
		logger.critical(e)
		raise e


def main():
	print "Testing S3 ..........."
	print "                      -> " + test_s3()
 	print "Testing Mandrill ....."
	print "                      -> " + test_mandril()
 	

	#sys.exit()
 
if __name__ == '__main__':
    main()





