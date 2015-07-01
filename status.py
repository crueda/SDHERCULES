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
#   libary boto (amazonS3)		To install: "pip install boto"
#   libary tinyS3 (amazonS3)	To install: "pip install tinys3"
#   libary mandrill 			To install: "pip install mandrill"
##################################################################################

import time
import sys
import os
import datetime
import logging, logging.handlers
import sqlalchemy
import uuid

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto
import tinys3

import mandrill

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

MANDRILL_KEY = config['mandrill_key']
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
def send2s3(file_name, complete_file_name):
	"""Envia un fichero a AmazonS3.

    Devuelve la url del fichero subido a S3

    Utiliza la credendiales en S3 definidas a nivel global

    Excepciones:
    IOError -- Si error al abrir el fichero

    """
	# Abrir el fichero
	try:
		f = open(complete_file_name,'rb') 

	    # Conectar con S3
		conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,tls=True, endpoint='s3-eu-west-1.amazonaws.com')
		logger.debug ("Conectado con S3")
		
		# Subir el fichero a S3
		conn.upload(file_name,f,S3_BUCKET,public=True)
		logger.debug ("Fichero subido a S3")
		
		# Construir la url
		s3_url_graph = S3_ENDPOINT + "/" + S3_BUCKET + "/" + file_name
		logger.debug ("URL del grafico en S3: " + s3_url_graph)
		return s3_url_graph
	except IOError as e:
		logger.error ("Error al acceder al fichero: error({0}): {1}".format(e.errno, e.strerror))


def send_mail_with_mandrill(template_name, template_content, message, send_at):
    mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)
    try:
        response = mandrill_client.messages.send_template(template_name=template_name,
                                                          template_content=template_content,
                                                          message=message,
                                                          send_at=send_at.strftime("%Y-%m-%d %H:%M:%S"))
        return response
    except Exception as e:
        logger.critical(e)
        raise e



def test_send_mail_template(template_name, email_to, context):
    mandrill_client = mandrill.Mandrill(MANDRILL_KEY)
    message = {
        'to': [],
        'global_merge_vars': []
    }
    for em in email_to:
        message['to'].append({'email': em})
 
    for k, v in context.iteritems():
        message['global_merge_vars'].append(
            {'name': k, 'content': v}
        )
    mandrill_client.messages.send_template(template_name, [], message)



def main():
	
	# Se envia a AmazonS3
	send2s3 ('test.png',GRAPHS_FOLDER + '/test.png')
 

 	# Envio de mail
 	#kwargs = {'api_key': MANDRILL_KEY, 'reply_to': 
 	#		'noreply@sd.com', 
 	#		'recipient': 'Recipient', 
 	#		'from_email': 'noreply@sd.com'
 	#}
	#send_mail(to=username, msg='Atención, detectado robo en su zona!', subj='Alerta de robo', **kwargs)

	# Intentos de envio de mail usando plantilla
 	#test_send_mail_template('template1', [username], context={'Name': "Bob Marley"})
 	#send_mail_template('template1', username)

	sys.exit()
 
if __name__ == '__main__':
    main()





