#!/usr/bin/env python
#-*- coding: UTF-8 -*-

# autor: Carlos Rueda
# date: 2015-04-07
# mail: carlos.rueda@deimos-space.com
# version: 1.0

##################################################################################
# version 1.0 release notes:
# Initial version
# Requisites: 
#	library configobj 			To install: "apt-get install python-configobj"
#	library matplotlib 			To install: "apt-get install python-matplotlib"
#   libary tinyS3 (amazonS3)	To install: "pip install tinys3"
##################################################################################

import time
import sys
import os
import datetime
import logging, logging.handlers
import uuid

#import matplotlib
from matplotlib.pyplot import *
from numpy import *

import pandas as pd
#import matplotlib.pyplot as plt

from matplotlib import pyplot
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange
from numpy import arange

from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np

import tinys3

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

def generate_uuid():
	return uuid.uuid1()



def test():
	x = linspace(0,5,50)
	y = x**2
	plot(x,y,'r')
	xlabel('x')
	#ylabel('y')
	title(u'Título') # el caracter `u` es necesario para incluir acentos en el texto
	show() # muestra el gráfico en una ventana, si no se ha usado %matplotlib inline

	fig = figure()

	ejes = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # izquierda, abajo, ancho, altura (rango 0 a 1)

	ejes.plot(x,y,'r')

	ejes.set_xlabel('x')
	ejes.set_ylabel('y')
	ejes.set_title(u'Robos/meses');


def graph1():
	logger.debug("Graph1")
	
	x = np.arange(12)
	robos = [12, 2, 5, 27, 2, 5, 8, 9, 12, 15, 34, 21]
	
	index = np.arange(12)
	bar_width = 0.8
	opacity = 1
	
	#my_colors = 'kkkkkkkkrkkk'  #red, green, blue, black, etc.

	my_colors = ('grey','grey','grey','grey','grey','grey','grey','red','grey','grey','grey','grey')
	plt.bar(index, robos, bar_width,
		alpha=opacity,
		color=my_colors)

	plt.yticks(robos, ['','','','','','','','','','','','' ]) 
	plt.xticks( x + 0.4,  ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12') )

	plt.title(u'Robos/meses');
	
	plt.box()
	
	'''
	plt.boxplot(plt, x, notch=False, sym='b+', vert=True, whis=1.5,
		positions=None, widths=None, patch_artist=False,
		bootstrap=None, usermedians=None, conf_intervals=None,
		meanline=False, showmeans=False, showcaps=True,
		showbox=True, showfliers=True, boxprops=None, labels=None,
		flierprops=None, medianprops=None, meanprops=None,
		capprops=None, whiskerprops=None, manage_xticks=True)
	'''

	plt.show()

	'''
	file_name = str(generate_uuid()) + '.png'
	complete_file_name = GRAPHS_FOLDER + '/' + file_name
	logger.debug ("Generando grafico: " + file_name)
	plt.savefig( complete_file_name )
	'''
	#return [file_name,complete_file_name]

def generate_graphs():
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

def send_s3_tiny(file_name, complete_file_name):
	conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,tls=True)
	logger.debug ("Conectado a S3")
	f = open(complete_file_name,'rb') 
	logger.debug ("Almacenando grafico en S3")
	conn.upload(file_name,f,S3_BUCKET,public=True)


def main():
	
	# Se generas los gráficos
	graph_files = generate_graphs()

	# Se envian a AmazonS3
	for file_name in graph_files:
		logger.debug ("Enviando a S3 el fichero: "+file_name)
		#send_s3_tiny (graph_file[0],graph_file[1])
		#s3_url_graph = "https://s3.amazonaws.com/" + S3_BUCKET + "/" + graph_file[0]
		#logger.debug ("Enviado!. URL en S3:" + s3_url_graph)
  		
 
if __name__ == '__main__':
	#main()
	#test()
	graph1()





