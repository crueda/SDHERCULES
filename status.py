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

#import matplotlib
from matplotlib import pyplot
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange
from numpy import arange

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto
import tinys3

import mandrill

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

#### VARIABLES #########################################################
from configobj import ConfigObj
config = ConfigObj('./sdhercules.properties')

INTERNAL_LOG_FILE = config['directory_logs'] + "/sdhercules.log"
LOG_FOR_ROTATE = 10

DB_HOST = config['mysql_host']
DB_PORT = config['mysql_port']
DB_NAME = config['mysql_db_name']
DB_USER = config['mysql_user']
DB_PASSWORD = config['mysql_passwd']

GRAPHS_FOLDER = config['directory_graphs']

S3_ACCESS_KEY = config['s3_keyId']
S3_SECRET_KEY = config['s3_secretKey']
S3_BUCKET = config['s3_bucket']

MANDRILL_KEY = config['mandrill_key']
########################################################################

#### LOGGER #########################################################
try:
	logger = logging.getLogger('sdhercules')
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

#### DDBB #########################################################
Base = declarative_base()

class NewsAviso(Base):
    __tablename__ = 'NEWS_AVISO'
    ID = Column(Integer, primary_key=True)
    CP = Column(Integer)
    TIMESTAMP = Column(Integer)
    IMAGEN1 = Column(Integer)
########################################################################

def generate_uuid():
	return uuid.uuid1()

def test_generate_graph():
	X = range(0,100)
	Y = [ i*i for i in X ]
	
	pyplot.plot( X, Y, '-' )
	pyplot.title( 'Numero de robos' )
	pyplot.xlabel( 'Dia' )
	pyplot.ylabel( 'Robos' )
	

	file_name = str(generate_uuid()) + '.png'
	complete_file_name = GRAPHS_FOLDER + '/' + file_name
	logger.debug ("Generando grafico: " + file_name)
	pyplot.savefig( complete_file_name )
	#pyplot.show()

	return [file_name,complete_file_name]

def generate_graph():
	date1 = datetime.datetime( 2000, 3, 2)
	date2 = datetime.datetime( 2000, 3, 6)
	delta = datetime.timedelta(hours=6)
	dates = drange(date1, date2, delta)
	
	y = arange( len(dates)*1.0)

	fig, ax = pyplot.subplots()
	ax.plot_date(dates, y*y)

	ax.set_xlim( dates[0], dates[-1] )

	ax.xaxis.set_major_locator( DayLocator() )
	ax.xaxis.set_minor_locator( HourLocator(arange(0,25,6)) )
	ax.xaxis.set_major_formatter( DateFormatter('%Y-%m-%d') )

	ax.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
	fig.autofmt_xdate()

	file_name = str(generate_uuid()) + '.png'
	complete_file_name = GRAPHS_FOLDER + '/' + file_name
	logger.debug ("Generando grafico: " + file_name)
	pyplot.savefig( complete_file_name )
	#pyplot.show()

	return [file_name,complete_file_name]

def percent_cb(complete, total):
    logger.debug('.')

def send_s3(file_name, complete_file_name):
	try:
		connS3 = boto.connect_s3(S3_ACCESS_KEY,S3_SECRET_KEY)
		logger.debug ("Conectado a S3")
		bucketS3 = connS3.get_bucket(S3_BUCKET)
		logger.debug ("Conectado a bucket")
		keyS3 = Key(bucketS3)
		keyS3.key = file_name
		logger.debug ("Almacenando grafico en S3")
		keyS3.set_contents_from_filename(complete_file_name,cb=percent_cb, num_cb=10)
		keyS3.make_public()
	except Exception, e:
		logger.error (str(e))
		return e		

def send_s3_tiny(file_name, complete_file_name):
	conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,tls=True)
	logger.debug ("Conectado a S3")
	f = open(complete_file_name,'rb') 
	logger.debug ("Almacenando grafico en S3")
	conn.upload(file_name,f,S3_BUCKET,public=True)

def send_s3cmd_os(file_name):
	command = "s3cmd put " + file_name + " s3://" + S3_BUCKET
	logger.debug ("Almacenando grafico en S3...")
	ret = os.system(command)
	if (ret == 0):
		logger.debug("Subido a S3 el fichero " + file_name)
	else:
		logger.error("Error al subir a S3 el fichero " + file_name)

	return ret

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

def send_mail_template(template_name, email_to):
	try:
		mandrill_client = mandrill.Mandrill(MANDRILL_KEY)
		template_content = [{'content': 'example content', 'name': 'example name'}]
		message = {'attachments': [{'content': 'ZXhhbXBsZSBmaWxl',
    								'name': 'myfile.txt',
    								'type': 'text/plain'}],
		'auto_html': None,
		'auto_text': None,
		'bcc_address': 'message.bcc_address@example.com',
		'from_email': 'message.from_email@example.com',
		'from_name': 'Example Name',
		'global_merge_vars': [{'content': 'merge1 content', 'name': 'merge1'}],
		'google_analytics_campaign': 'message.from_email@example.com',
		'google_analytics_domains': ['example.com'],
		'headers': {'Reply-To': 'message.reply@example.com'},
		'html': '<p>Example HTML content</p>',
		'images': [{'content': 'ZXhhbXBsZSBmaWxl',
		'name': 'IMAGECID',
		'type': 'image/png'}],
		'important': False,
		'inline_css': None,
		'merge': True,
		'merge_language': 'mailchimp',
		'merge_vars': [{'rcpt': 'recipient.email@example.com',
					'vars': [{'content': 'merge2 content', 'name': 'merge2'}]}],
		'metadata': {'website': 'www.example.com'},
		'preserve_recipients': None,
		'recipient_metadata': [{'rcpt': 'recipient.email@example.com',
					'values': {'user_id': 123456}}],
		'return_path_domain': None,
		'signing_domain': None,
		'subaccount': 'customer-123',
		'subject': 'example subject',
		'tags': ['password-resets'],
		'text': 'Example text content',
		'to': [{'email': email_to,
				'name': 'Recipient Name',
				'type': 'to'}],
		'track_clicks': None,
		'track_opens': None,
		'tracking_domain': None,
		'url_strip_qs': None,
		'view_content_link': None}

		result = mandrill_client.messages.send_template(template_name=template_name, template_content=template_content, message=message, async=False, ip_pool='Main Pool')
		print result
		'''
		[{'_id': 'abc123abc123abc123abc123abc123',
		'email': 'recipient.email@example.com',
		'reject_reason': 'hard-bounce',
		'status': 'sent'}]
		'''

	except mandrill.Error, e:
    	# Mandrill errors are thrown as exceptions
		print 'A mandrill error occurred: %s - %s' % (e.__class__, e)
		# A mandrill error occurred: <class 'mandrill.UnknownSubaccountError'> - No subaccount exists with the id 'customer-123'    
		raise

def send_mail(to, subj, msg, **kwargs):
    """ Sends the message by posting to Mandrill API

        @param to: the recipient for the message
        @type to: str

        @param subj: the subject for the email
        @type subj: str

        @param msg: the body of the message, in plain text
        @type msg: str

        @param kwargs: other settings, compliant with Mandrill API
        @type kwargs: dict

        @see: https://mandrillapp.com/api/docs/
    """
    # TODO: use Jinja templates for the HTML body ??
    msg = {
        'from_email': kwargs.get('from_email'),
        'from_name': 'Securitas Direct Newsletter - Alerta de Robo',
        'html': '<h3>Alerta automática de robo en su zona</h3><p>{msg}</p><h6>Sent by Securitas Direct'
                ' &copy; 2015</h6>'.format(msg=msg),
        'headers': {'Reply-To': kwargs.get('reply_to')},
        'subject': subj,
        'to': [
            {'email': to,
             'name': kwargs.get('recipient'),
             'type': 'to'
            }
        ]
    }
    mc = mandrill.Mandrill(kwargs.get('api_key'))
    try:
    	logger.debug ("Enviando mail a: " + to)
        res = mc.messages.send(msg, async=kwargs.get('async', False))
        if res and not res[0].get('status') == 'sent':
            logging.error('Could not send email to {to}; status: {status}, reason: {reason}'
                          .format(to=to, status=res.get('status', 'unknown'),
                                  reason=res.get('reject_reason')))
            exit(1)
    except mandrill.Error, e:
        # Mandrill errors are thrown as exceptions
        logging.error('A mandrill error occurred: {} - {}'.format(e.__class__.__name__, e))
        exit(1)
    logging.info('Message sent to {to}'.format(to=to))

def insert_newsAviso (cp, url_image1):

	engine = create_engine('mysql://' + DB_USER + ':' + DB_PASSWORD + '@' + DB_HOST + '/' + DB_NAME, pool_recycle=3600)
	 
	session = sessionmaker()
	session.configure(bind=engine)
	Base.metadata.create_all(engine)

	logger.debug ("Insertando newsAviso en bbdd")
	aviso = NewsAviso(CP=cp, IMAGEN1=url_image1)
	s = session()
	s.add(aviso)
	s.commit()
	s.flush()


def main():
	
	if (len(sys.argv) == 3):
		username = sys.argv[1]
		cp = sys.argv[2]

		# Se genera el gráfico
		graph_file = generate_graph()

		# Se envia a AmazonS3
		send_s3_tiny (graph_file[0],graph_file[1])
		s3_url_graph = "https://s3.amazonaws.com/" + S3_BUCKET + "/" + graph_file[0]
		logger.debug ("URL en S3:" + s3_url_graph)
 

 		# Envio de mail
 		kwargs = {'api_key': MANDRILL_KEY, 'reply_to': 
 			'noreply@sd.com', 
 			'recipient': 'Recipient', 
 			'from_email': 'noreply@sd.com'
 		}
		send_mail(to=username, msg='Atención, detectado robo en su zona!', subj='Alerta de robo', **kwargs)

		# Intentos de envio de mail usando plantilla
 		#test_send_mail_template('template1', [username], context={'Name': "Bob Marley"})
 		#send_mail_template('template1', username)

 		# se inserta en la base de datos
 		insert_newsAviso (cp, s3_url_graph)

	else: 
		print "usage:   python sdhercules.py <suscriptor-email> <postal-code>"
		print "example: python sdhercules.py carm@sd.clientes.com 28080"
		sys.exit()
 
if __name__ == '__main__':
    main()





