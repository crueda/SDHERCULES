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
import gc

#import matplotlib
from matplotlib.pyplot import *
from numpy import *

from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import argrelextrema

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

S3_ENDPOINT = config['s3_endpoint']
S3_ACCESS_KEY = config['s3_keyId']
S3_SECRET_KEY = config['s3_secretKey']
S3_BUCKET = config['s3_bucket']

COLOR_RED = '#E30613' 
COLOR_GREY = '#F3F3F3' 


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
	#except:
		#logger.error ("Unexpected error: " + sys.exc_info()[0])
		#raise

def send_s3_tiny(file_name, complete_file_name):
	conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,tls=True)
	logger.debug ("Conectado a S3")
	f = open(complete_file_name,'rb') 
	logger.debug ("Almacenando grafico en S3")
	conn.upload(file_name,f,S3_BUCKET,public=True)
	
########################################################################
# PRIMER GRAFICO
#
# Grafico de barras. Robos por meses
#
#
########################################################################
def grafico_robos_meses(graph_data_x, graph_data_y):
	logger.debug("grafico_robos_meses - grafico 1")
	
	# Definir la figura
	fig = plt.figure()

	ax = fig.add_subplot(1, 1, 1)

	# Fijar el tamano de la figura (en pulgadas)

	#fig.set_size_inches(2.667, 1.514)
	fig.set_size_inches(2.355, 1.350)
	fig.tight_layout()

	#fig.set_size_inches(1.690/1.320, 1, forward=True)
	#fig.set_size_inches(2.667/1.514, 1, forward=True)

	index = np.arange(12)
	bar_width = 0.8
	opacity = 1
	
	# Fijar el array de colores
	value_max = np.max(graph_data_y)
	my_colors = []
	for i in range(12):
		if graph_data_y[i]<value_max:
			my_colors.append(COLOR_GREY)
		else:
			my_colors.append(COLOR_RED)

	plt.bar(index, graph_data_y, bar_width,
		alpha=opacity,
		linewidth=0,
		color=my_colors)

	x = np.arange(12)
		
	# Marcas de los ejes
	dias = np.arange(7)
	plt.xticks( x + 0.4,  graph_data_x, fontsize=7, rotation=55)

	# Eje X
	plt.axhline(y=0, linewidth=2, linestyle='-', color='grey')
	
	# Color de la fuente en los ejes
	ax.tick_params(axis='x', labelcolor='#757172')

	# Ajustar el eje x
	plt.tick_params( axis='x',          
		which='both',     
    	bottom='on',      
    	top='off',     
		direction='inout',
		color=COLOR_GREY,    
    	labelbottom='on')

	# Marcas del eje x
	for t in ax.xaxis.iter_ticks():
		t[0].tick1line.set_marker(u'o')
		
	# Ocultar el eje y
	plt.tick_params( axis='y',          
		which='both',      
    	left='off',      
    	right='off',        
    	labelleft='off') 

	# Fijar el limite inferior de la grafica
	plt.ylim(ymin=0)

	# Eliminar el borde
	plt.box()
	
	# Mostrar grafico en GUI (desarrollo)
	#plt.show()
	
	# Generar el fichero
	file_name = str(generate_uuid()) + '.png'
	complete_file_name = GRAPHS_FOLDER + '/' + file_name
	logger.debug ("Generando grafico: " + file_name)
	plt.savefig( complete_file_name, transparent=True,  bbox_inches='tight')
	
	# liberar memoria
	fig.clf()    
	plt.close()
	del ax, index, graph_data_y
	gc.collect()
	
	# Subir a S3
	#send2s3 (file_name, complete_file_name)
	
	return [S3_ENDPOINT, S3_BUCKET, file_name]
	
	

########################################################################
# SEGUNDO GRAFICO
#
# Grafico de linea. Rodos por dia de la semana
#
#
########################################################################
def grafico_robos_semana(graph_data_x, graph_data_y):
	logger.debug("grafico_robos_semana - grafico 2")
	
	# Definir la figura
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)

	# Fijar el tamano de la figura (en pulgadas)
	#fig.set_size_inches(2.778, 1.514)
	fig.set_size_inches(2.418, 1.440)
	fig.tight_layout()

	# Grafico
	dias = np.arange(7)
	plt.plot(dias, graph_data_y,  linestyle='-', color='r', linewidth=2)

	# Marcas de los ejes
	dias = np.arange(7)
	plt.xticks( dias, graph_data_x, fontsize=8 )
	
	# Eje X 
	plt.axhline(y=0, linewidth=2, linestyle='-', color='grey')
	
	# Color de la fuente en los ejes
	ax.tick_params(axis='x', labelcolor='#757172')

	# Ajustar el eje x
	plt.tick_params( axis='x',          
		which='both',     
    	bottom='on',      
    	top='off',  
		direction='inout',
		color=COLOR_GREY,       
    	labelbottom='on')

	# Marcas del eje x
	for t in ax.xaxis.iter_ticks():
		t[0].tick1line.set_marker(u'o')
		
	# Ocultar el eje y
	plt.tick_params( axis='y',          
		which='both',      
    	left='off',      
    	right='off',        
    	labelleft='off') 

	# Fijar el limite inferior de la grafica
	plt.ylim(ymin=0)

	# Ajustar el limite superior -> incremento un 5% para que no se corte arriba
	value_max = np.max(graph_data_y)
	plt.ylim(ymax=value_max*1.05)

	# ocultar borde exterior
	plt.box()

	# Mostrar grafico en GUI (desarrollo)
	#plt.show()

	# Generar el fichero
	file_name = str(generate_uuid()) + '.png'
	complete_file_name = GRAPHS_FOLDER + '/' + file_name
	logger.debug ("Generando grafico: " + file_name)
	plt.savefig( complete_file_name, transparent=True, bbox_inches='tight')

	# liberar memoria
	fig.clf()    
	plt.close()
	del ax, dias, graph_data_x, graph_data_y
	gc.collect()
	
	# Subir a S3
	#send2s3 (file_name, complete_file_name)
	
	return [S3_ENDPOINT, S3_BUCKET, file_name]
	
	
########################################################################
# TERCER GRAFICO
#
# Grafico de barras. Robos dia/noche
#
#
########################################################################
def grafico_robos_dia(graph_data_x, graph_data_y):
	logger.debug("grafico_robos_dia - grafico 3")

	# Ajustar los datos del eje x
	axis_x_data = graph_data_x
	axis_x_data.insert(1, '')

	# Ajustar los datos del eje y
	axis_y_data = graph_data_y
	axis_y_data.insert(1, 0)
	
	# Definir la figura
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)

	# Fijar el tamano de la figura (en pulgadas)
	#fig.set_size_inches(1.542, 1.5)
	fig.set_size_inches(1.660, 1.335)
	fig.tight_layout()

	x = np.arange(3)
	index = np.arange(3)
	bar_width = 0.8
	opacity = 1
	
	# Dibujar el gráfico
	if (graph_data_y[0]<graph_data_y[2]):
		my_colors = (COLOR_GREY, COLOR_GREY, COLOR_RED)
	else:
		my_colors = (COLOR_RED, COLOR_GREY, COLOR_GREY)

	fig = plt.bar(index, axis_y_data, bar_width,
		alpha=opacity,
		linewidth=0,
		color=my_colors)

	# Marcas de los ejes
	plt.xticks( x + 0.4, axis_x_data, fontsize=8 )

	# Eje X
	plt.axhline(y=0, linewidth=2, linestyle='-', color='grey')
	
	# Color de la fuente en los ejes
	ax.tick_params(axis='x', labelcolor='#757172')

	# Ajustar el eje x
	plt.tick_params( axis='x',          
		which='both',     
    	bottom='on',      
    	top='off',         
		direction='inout',
		color=COLOR_GREY,
    	labelbottom='on')

	# Marcas del eje x
	for t in ax.xaxis.iter_ticks():
		t[0].tick1line.set_marker(u'')

	# Ocultar el eje y
	plt.tick_params( axis='y',          
		which='both',      
    	left='off',      
    	right='off',        
    	labelleft='off') 

	# Fijar el limite inferior de la grafica
	plt.ylim(ymin=0)

	# ocultar borde exterior
	plt.box()

	# Textos sobre las barras (porcentajes de robos)
	for rect in fig:
		height = rect.get_height()
		if (int(height)>0):		
			plt.text(rect.get_x()+rect.get_width()/2., height+5, '%d'%int(height)+'%', ha='center', va='bottom', fontsize=6)

	# Mostrar grafico en GUI (desarrollo)
	#plt.show()

	# Generar el fichero
	file_name = str(generate_uuid()) + '.png'
	complete_file_name = GRAPHS_FOLDER + '/' + file_name
	logger.debug ("Generando grafico: " + file_name)
	plt.savefig( complete_file_name, transparent=True, bbox_inches='tight')
	
	# liberar memoria
	plt.close()
	del ax, index, axis_y_data
	gc.collect()

	# Subir a S3
	#send2s3 (file_name, complete_file_name)
	
	return [S3_ENDPOINT, S3_BUCKET, file_name]
	
	

########################################################################
# CUARTO GRAFICO
#
# Grafico de linea con el historico anual + prevision
#
#
########################################################################
def grafico_historial_robos(graph_data_x, graph_data_y, graph_data2_x, graph_data2_y):
	logger.debug("grafico_robos_dia - grafico 4")
	
	meses = np.arange(13)
	meses_extendido = np.arange(16)
	
	robos_extendido =  graph_data_y + graph_data2_y
	label_meses_extendido = graph_data_x + graph_data2_x

	# Definir la figura
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)

	# Fijar el tamano de la figura (en pulgadas)
	#fig.set_size_inches(7.681, 3.556)
	fig.set_size_inches(5.770, 2.570)
	fig.tight_layout()

	
	# Marcas del eje x
	plt.xticks( meses_extendido + 0,  label_meses_extendido, fontsize=12, rotation=45)
	
	# Dibujar el grafico
	plt.plot(meses, graph_data_y, 'b-', color='r', linewidth=2)	
	plt.plot(meses_extendido, robos_extendido, 'b--', color='r', linewidth=2)

	# Eje X
	plt.axhline(y=0, xmax=0.8, linewidth=3, linestyle='-', color='grey')
	plt.axhline(y=0, xmin=0.8, linewidth=3, linestyle='--', color='grey')
	
	# ocultar eje x superior
	ax.spines['top'].set_visible(False)
	
	# Color de la fuente en los ejes
	ax.tick_params(axis='x', labelcolor='#757172')
	ax.tick_params(axis='y', labelcolor='#757172')

	# Ajustar el eje x
	plt.tick_params(axis='x',
    	which='both',
    	bottom='on',
    	top='off',
    	direction='inout',
    	color=COLOR_GREY,
    	labelbottom='on')

	# Marcas del eje x
	for t in ax.xaxis.iter_ticks():
		t[0].tick1line.set_marker(u'o')

	# Ocultar el eje y
	plt.tick_params( axis='y',          
		which='both',      
    	left='off',      
    	right='off',        
    	labelleft='off') 

	# Fijar el limite inferior de la grafica
	plt.ylim(ymin=0)

	# Ajustar el limite superior -> incremento un 20%
	#value_max = np.max(graph_data_y)
	value_max = np.max(graph_data_y + graph_data2_y)
	plt.ylim(ymax=value_max*1.2)

	# ocultar el borde del gráfico
	plt.box()
	
	# Buscamos los maximos locales
	valores = np.array([graph_data_y[0]])
	for i in range(1, 11):
		valores = np.concatenate((valores, np.array([graph_data_y[i]])))	
	maximos = argrelextrema(valores, np.greater)[0]


	# Pintar los maximos en la grafica
	for index_max in maximos:
		bbox_props = dict(boxstyle="round", fc="grey", ec="0.9", alpha=0)
		if (graph_data_y[index_max]<10):
			t= ax.text(index_max-0.1, graph_data_y[index_max]+ (value_max*0.3)/ 7 ,graph_data_y[index_max], bbox=bbox_props, fontsize=8, color='k')
		else:
			t= ax.text(index_max-0.2, graph_data_y[index_max]+ (value_max*0.3)/ 7 ,graph_data_y[index_max], bbox=bbox_props, fontsize=8, color='k')

		plt.axvline(x=index_max, ymin=0, ymax =float(float(graph_data_y[index_max])/float(value_max*1.2)), linewidth=1, linestyle=':', color='grey')
		
		#print float((2.1/float(value_max)))
		#plt.scatter(index_max, graph_data_y[index_max]+float((2.7/float(value_max))), s=500, facecolors='none', edgecolors='grey', linestyle=':')
		#plt.scatter(index_max, graph_data_y[index_max], s=500, facecolors='none', edgecolors='grey', linestyle=':')

	# Mostrar grafico en GUI (desarrollo)
	#plt.show()
	
	
	# Generar el fichero	
	file_name = str(generate_uuid()) + '.png'
	complete_file_name = GRAPHS_FOLDER + '/' + file_name
	logger.debug ("Generando grafico: " + file_name)
	plt.savefig( complete_file_name, transparent=True, bbox_inches='tight')
	
	# liberar memoria
	fig.clf()    
	plt.close()
	del ax, meses, meses_extendido, graph_data_y, robos_extendido
	gc.collect()

	# Subir a S3
	#send2s3 (file_name, complete_file_name)
	
	return [S3_ENDPOINT, S3_BUCKET, file_name]
	
	


def main():
	
	graph1_data_x = ['APR-05', 'MAY-05', 'JUN-05', 'JUL-05', 'AUG-05', 'SEP-05', 'OCT-05', 'NOV-05', 'DEC-05', 'JAN-05', 'FEB-05', 'MAR-05']
	graph1_data_y = [7, 4, 2, 3, 7, 2, 3, 2, 4, 2, 3, 4]
	#grafico_robos_meses(graph1_data_x, graph1_data_y)

	graph2_data_x = ['LUN', 'MAR', 'MIER', 'JUE', 'VIER', 'SAB', 'DOM']
	graph2_data_y = [2, 3, 4, 4, 6, 0, 1]
	#grafico_robos_semana(graph2_data_x, graph2_data_y)
	
	graph3_data_x = ['Dia', 'Noche']
	graph3_data_y = [15, 85]
	#grafico_robos_dia(graph3_data_x, graph3_data_y)
	
	graph4_data_x = ['ABR-14', 'MAY-14', 'JUN-14', 'JUL-14', 'AGO-14', 'SEP-14', 'OCT-14', 'NOV-14', 'DIC-14', 'ENE-15', 'FEB-15', 'MAR-15', 'ABR-15']
	graph4_data_y = [120, 230, 200, 230, 173, 217, 259, 273, 282, 249, 244, 288, 422.0]
	graph4_data2_x = ['MAY-15', 'JUN-15', 'JUL-15']
	graph4_data2_y = [387.0, 359.0, 406.0]
	#graph4_data_y = [21, 13, 4, 23, 11, 10, 8, 7, 9, 12, 8, 5]
	#graph4_data2_y = [4, 2, 2, 5]
	grafico_historial_robos(graph4_data_x, graph4_data_y, graph4_data2_x, graph4_data2_y)




if __name__ == '__main__':
	main()
	#test()

	





