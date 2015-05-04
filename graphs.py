from datetime import date, timedelta
from dateutil import relativedelta
from django.conf import settings
import gc
from django.db.models import Count
import tinys3

from .models import Incidence, IncidenceStatisticImage, KeyVal
import locale
import logging
import uuid
from numpy import *
from scipy.signal import argrelextrema

import matplotlib as mpl

mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
# Get an instance of a logger
logger = logging.getLogger('incidences.generate_images')

GRAPHS_FOLDER = settings.GRAPHS_FOLDER

S3_ENDPOINT = settings.S3_ENDPOINT
S3_ACCESS_KEY = settings.S3_ACCESS_KEY
S3_SECRET_KEY = settings.S3_SECRET_KEY
S3_BUCKET = settings.S3_BUCKET_GRAPHICS

COLOR_RED = '#ff0020'  # Pantone Coated 485 C
COLOR_GREY = '#949394'  # Pantone Coated 7545 C

########################################################################
# Funciones auxiliares
#
########################################################################


def generate_uuid():
    return uuid.uuid1()


def send2s3(file_name, complete_file_name):
    """Envia un fichero a AmazonS3.

    Devuelve la url del fichero subido a S3

    Utiliza la credendiales en S3 definidas a nivel global

    Excepciones:
    IOError -- Si error al abrir el fichero

    """
    # Abrir el fichero
    try:
        f = open(complete_file_name, 'rb')

        conn = tinys3.Connection(S3_ACCESS_KEY, S3_SECRET_KEY, tls=True, endpoint='s3-eu-west-1.amazonaws.com')
        logger.debug("Conectado con S3")

        conn.upload(file_name, f, S3_BUCKET, public=True)
        logger.debug("Fichero subido a S3")

        s3_url_graph = S3_ENDPOINT + "/" + S3_BUCKET + "/" + file_name
        logger.debug("URL del grafico en S3: " + s3_url_graph)
        return s3_url_graph
    except IOError as e:
        logger.error("Error al acceder al fichero: error({0}): {1}".format(e.errno, e.strerror))
        # except:
        # logger.error ("Unexpected error: " + sys.exc_info()[0])
        # raise


########################################################################
# PRIMER GRAFICO
#
# Grafico de barras. Robos por meses
#
#
########################################################################
def grafico_robos_meses(graph_data_x, graph_data_y):
    logger.debug("grafico_robos_meses - grafico 1")

    fig = plt.figure()

    ax = fig.add_subplot(1, 1, 1)

    fig.set_size_inches(2.355, 1.350)
    fig.tight_layout()

    index = np.arange(12)
    bar_width = 0.8
    opacity = 1

    value_max = np.max(graph_data_y)
    my_colors = []
    for i in range(12):
        if graph_data_y[i] < value_max:
            my_colors.append(COLOR_GREY)
        else:
            my_colors.append(COLOR_RED)

    plt.bar(index, graph_data_y, bar_width,
            alpha=opacity,
            linewidth=0,
            color=my_colors)

    x = np.arange(12)

    plt.xticks(x + 0.4, graph_data_x, fontsize=8, rotation=55)

    plt.axhline(y=0, linewidth=2, linestyle='-', color='grey')

    ax.tick_params(axis='x', labelcolor='#757172')

    plt.tick_params(axis='x',
                    which='both',
                    bottom='on',
                    top='off',
                    direction='inout',
                    color=COLOR_GREY,
                    labelbottom='on')

    plt.tick_params(axis='y',
                    which='both',
                    left='off',
                    right='off',
                    labelleft='off')

    for t in ax.xaxis.iter_ticks():
        t[0].tick1line.set_marker(u'')

    plt.ylim(ymin=0)

    plt.box()

    file_name = str(generate_uuid()) + '.png'
    complete_file_name = GRAPHS_FOLDER + '/' + file_name
    logger.debug("Generando grafico: " + file_name)
    plt.savefig(complete_file_name, transparent=True, bbox_inches='tight')

    fig.clf()
    plt.close()
    del ax, index, graph_data_y
    gc.collect()

    return S3_ENDPOINT, S3_BUCKET, file_name


########################################################################
# SEGUNDO GRAFICO
#
# Grafico de linea. Rodos por dia de la semana
#
#
########################################################################


def grafico_robos_semana(graph_data_x, graph_data_y):
    logger.debug("grafico_robos_semana - grafico 2")

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    fig.set_size_inches(2.418, 1.440)
    fig.tight_layout()

    dias = np.arange(7)
    plt.plot(dias, graph_data_y, linestyle='-', color='r', linewidth=2)

    plt.xticks(dias, graph_data_x, fontsize=8)

    plt.axhline(y=0, linewidth=2, linestyle='-', color='grey')

    ax.tick_params(axis='x', labelcolor='#757172')

    plt.tick_params(axis='x',
                    which='both',
                    bottom='on',
                    top='off',
                    direction='inout',
                    color=COLOR_GREY,
                    labelbottom='on')

    for t in ax.xaxis.iter_ticks():
        t[0].tick1line.set_marker(u'o')

    plt.tick_params(axis='y',
                    which='both',
                    left='off',
                    right='off',
                    labelleft='off')

    plt.ylim(ymin=0)

    value_max = np.max(graph_data_y)
    plt.ylim(ymax=value_max * 1.05)

    plt.box()

    file_name = str(generate_uuid()) + '.png'
    complete_file_name = GRAPHS_FOLDER + '/' + file_name
    logger.debug("Generando grafico: " + file_name)
    plt.savefig(complete_file_name, transparent=True, bbox_inches='tight')

    fig.clf()
    plt.close()
    del ax, dias, graph_data_x, graph_data_y
    gc.collect()

    return S3_ENDPOINT, S3_BUCKET, file_name


########################################################################
# TERCER GRAFICO
#
# Grafico de barras. Robos dia/noche
#
#
########################################################################

def grafico_robos_dia(graph_data_x, graph_data_y):
    logger.debug("grafico_robos_dia - grafico 3")  # Ajustar los datos del eje x
    axis_x_data = graph_data_x
    axis_x_data.insert(1, '')

    axis_y_data = graph_data_y
    axis_y_data.insert(1, 0)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    fig.set_size_inches(1.660, 1.335)
    fig.tight_layout()

    x = np.arange(3)
    index = np.arange(3)
    bar_width = 0.8
    opacity = 1

    if graph_data_y[0] < graph_data_y[2]:
        my_colors = (COLOR_GREY, COLOR_GREY, COLOR_RED)
    else:
        my_colors = (COLOR_RED, COLOR_GREY, COLOR_GREY)

    fig = plt.bar(index, axis_y_data, bar_width,
                  alpha=opacity,
                  linewidth=0,
                  color=my_colors)

    plt.xticks(x + 0.4, axis_x_data, fontsize=8)

    plt.axhline(y=0, linewidth=2, linestyle='-', color='grey')

    ax.tick_params(axis='x', labelcolor='#757172')

    plt.tick_params(axis='x',
                    which='both',
                    bottom='on',
                    top='off',
                    direction='inout',
                    color=COLOR_GREY,
                    labelbottom='on')

    for t in ax.xaxis.iter_ticks():
        t[0].tick1line.set_marker(u'')

    plt.tick_params(axis='y',
                    which='both',
                    left='off',
                    right='off',
                    labelleft='off')

    plt.ylim(ymin=0)

    plt.box()

    for rect in fig:
        height = rect.get_height()
        if int(height) > 0:
            plt.text(rect.get_x() + rect.get_width() / 2., height + 5, '%d' % int(height) + '%', ha='center',
                     va='bottom', fontsize=7)

    file_name = str(generate_uuid()) + '.png'
    complete_file_name = GRAPHS_FOLDER + '/' + file_name
    logger.debug("Generando grafico: " + file_name)
    plt.savefig(complete_file_name, transparent=True, bbox_inches='tight')

    plt.close()
    del ax, index, axis_y_data
    gc.collect()

    return S3_ENDPOINT, S3_BUCKET, file_name


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

    fig = plt.figure()

    robos_extendido = graph_data_y + graph_data2_y
    label_meses_extendido = graph_data_x + graph_data2_x

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    fig.set_size_inches(5.770, 2.570)
    fig.tight_layout()

    plt.xticks(meses_extendido + 0, label_meses_extendido, fontsize=8, rotation=45)

    plt.plot(meses, graph_data_y, 'b-', color='r', linewidth=2)
    plt.plot(meses_extendido, robos_extendido, 'b--', color='r', linewidth=2)

    plt.axhline(y=0, xmax=0.8, linewidth=3, linestyle='-', color='grey')
    plt.axhline(y=0, xmin=0.8, linewidth=3, linestyle='--', color='grey')

    ax.spines['top'].set_visible(False)

    ax.tick_params(axis='x', labelcolor='#757172')
    ax.tick_params(axis='y', labelcolor='#757172')

    plt.tick_params(axis='x',
                    which='both',
                    bottom='on',
                    top='off',
                    direction='inout',
                    color=COLOR_GREY,
                    labelbottom='on')

    for t in ax.xaxis.iter_ticks():
        t[0].tick1line.set_marker(u'o')

    plt.tick_params(axis='y',
                    which='both',
                    left='off',
                    right='off',
                    labelleft='off')

    plt.ylim(ymin=0)

    value_max = np.max(graph_data_y + graph_data2_y)
    plt.ylim(ymax=value_max * 1.2)

    plt.box()

    valores = np.array([graph_data_y[0]])
    for i in range(1, 11):
        valores = np.concatenate((valores, np.array([graph_data_y[i]])))
    maximos = argrelextrema(valores, np.greater)[0]

    for index_max in maximos:
        bbox_props = dict(boxstyle="round", fc="grey", ec="0.9", alpha=0.5)
        if graph_data_y[index_max] < 10:
            t = ax.text(index_max - 0.1, graph_data_y[index_max] + (value_max * 0.3) / 7, graph_data_y[index_max],
                        bbox=bbox_props,
                        fontsize=7, color='k')
        else:
            t = ax.text(index_max - 0.2, graph_data_y[index_max] + (value_max * 0.3) / 7, graph_data_y[index_max],
                        bbox=bbox_props,
                        fontsize=7, color='k')

        plt.axvline(x=index_max, ymin=0, ymax=float(float(graph_data_y[index_max]) / float(value_max*1.2)),
                    linewidth=1, linestyle=':', color='grey')

    file_name = str(generate_uuid()) + '.png'
    complete_file_name = GRAPHS_FOLDER + '/' + file_name
    logger.debug("Generando grafico: " + file_name)
    plt.savefig(complete_file_name, transparent=True, bbox_inches='tight')

    fig.clf()
    plt.close()
    del ax, meses, meses_extendido, graph_data_y, robos_extendido
    gc.collect()

    return S3_ENDPOINT, S3_BUCKET, file_name


class GraphGenerator(object):
    def __init__(self, province, ref_date=date.today(), locale_code=settings.LANGUAGE_CODE):
        self._province = province
        self._ref_date = ref_date
        self._incidences = Incidence.objects.filter(location__province=self._province)
        self._locale_code = locale_code

    def get_monthly_theft_by_province(self):
        incidences = self._incidences.filter()

        locale.setlocale(locale.LC_ALL, self._locale_code)

        x_axis = []
        y_axis = []

        for m in range(1, 13):
            x_axis.append('%s' % locale.nl_langinfo(getattr(locale, 'ABMON_%s' % m)).upper())
            y_axis.append(incidences.filter(police_date__month=m).count() / len(
                incidences.filter(police_date__month=m).extra(
                    select={'year': 'EXTRACT(YEAR FROM "police_date")'}).values('year').distinct()))

        host, bucket, file_name = grafico_robos_meses(x_axis, y_axis)

        incidence_statistic = IncidenceStatisticImage.objects.create(province=self._province,
                                                                     type=IncidenceStatisticImage.MONTHLY_THEFTS,
                                                                     host=host,
                                                                     bucket=bucket,
                                                                     name=file_name)

        return incidence_statistic

    def get_week_daily_theft_by_province(self, delta_days=-30):
        incidences = self._incidences.filter(
            police_date__range=(self._ref_date + timedelta(days=delta_days), self._ref_date))

        locale.setlocale(locale.LC_ALL, self._locale_code)

        x_axis = []
        y_axis = []
        for wd in range(2, 8) + [1]:
            x_axis.append(locale.nl_langinfo(getattr(locale, 'ABDAY_%s' % wd)).decode('UTF8').upper())
            y_axis.append(incidences.filter(police_date__week_day=wd).count())

        host, bucket, file_name = grafico_robos_semana(x_axis, y_axis)

        incidence_statistic = IncidenceStatisticImage.objects.create(province=self._province,
                                                                     type=IncidenceStatisticImage.WEEKLY_THEFTS,
                                                                     host=host,
                                                                     bucket=bucket,
                                                                     name=file_name)

        return incidence_statistic

    def get_monthly_theft_by_province_with_prediction(self, delta_days=-365):
        incidences = self._incidences.filter(
            police_date__range=(self._ref_date + timedelta(days=delta_days), self._ref_date))
        locale.setlocale(locale.LC_ALL, self._locale_code)
        x_axis = []
        y_axis = []
        x_axis2 = []
        y_axis2 = []

        for m in range(self._ref_date.month, 13):
            x_axis.append(('%s-%d' % (
                locale.nl_langinfo(
                    getattr(locale, 'ABMON_%s' % m)), (self._ref_date.year - 1) % 100)).upper())
            y_axis.append(incidences.filter(police_date__month=m).count())

        for m in range(1, self._ref_date.month):
            x_axis.append(('%s-%d' % (
                locale.nl_langinfo(
                    getattr(locale, 'ABMON_%s' % m)), self._ref_date.year % 100)).upper())
            y_axis.append(incidences.filter(police_date__month=m).count())

        historical_thefts_count = self._incidences.filter(police_date__gte=date(2014, 1, 1)).count()
        months = relativedelta.relativedelta(self._ref_date, date(2014, 1, 1)).months + relativedelta.relativedelta(
            self._ref_date, date(2014, 1, 1)).years * 12
        historical_thefts_avg = historical_thefts_count / months

        aux = self._incidences.filter(police_date__gte=date(2014, 1, 1)).extra(
            select={'year': 'EXTRACT(YEAR FROM "police_date")', 'month': 'EXTRACT(MONTH FROM "police_date")'}).values(
            'year', 'month').annotate(count=Count('police_date'))
        count_aux = [x['count'] for x in aux]
        min_count = min(count_aux)
        max_count = max(count_aux)

        del aux, count_aux

        x_axis.append(('%s-%d' % (
            locale.nl_langinfo(
                getattr(locale, 'ABMON_%s' % self._ref_date.month)), self._ref_date.year % 100)).upper())
        month_coef = (((self._incidences.filter(police_date__year=self._ref_date.year - 1,
                                                police_date__month=self._ref_date.month).count() - min_count) * 0.7) / (
            max_count - min_count)) + 0.8
        # forecast = [historical_thefts_avg * (1 + settings.GROWTH_RATE_THEFT[self._ref_date.month - 1]) * month_coef]
        y_axis.append(
            math.ceil(historical_thefts_avg * (1 + settings.GROWTH_RATE_THEFT[self._ref_date.month - 1]) * month_coef))

        for m in range(self._ref_date.month + 1, self._ref_date.month + 4):
            y = self._ref_date.year if m <= 12 else self._ref_date.year + 1
            m = m if m <= 12 else m - 12

            month_coef = (((self._incidences.filter(police_date__year=y - 1,
                                                    police_date__month=m).count() - min_count) * 0.7) / (
                max_count - min_count + 0.8)) + 0.8

            x_axis2.append(('%s-%d' % (
                locale.nl_langinfo(
                    getattr(locale, 'ABMON_%s' % m)), y % 100)).upper())
            '''
            if len(y_axis2) == 0:
                forecast.append(historical_thefts_avg * (1 + settings.GROWTH_RATE_THEFT[m - 1]) * month_coef)
            else:
                forecast.append(historical_thefts_avg * (1 + settings.GROWTH_RATE_THEFT[m - 1]) * month_coef)
            '''

            y_axis2.append(math.ceil(historical_thefts_avg * (1 + settings.GROWTH_RATE_THEFT[m - 1]) * month_coef))

        host, bucket, file_name = grafico_historial_robos(x_axis, y_axis, x_axis2, y_axis2)

        incidence_statistic = IncidenceStatisticImage.objects.create(province=self._province,
                                                                     type=IncidenceStatisticImage.MONTHLY_THEFTS_WITH_PREDICTION,
                                                                     host=host,
                                                                     bucket=bucket,
                                                                     name=file_name)

        return incidence_statistic

    def get_day_and_night_by_province(self, delta_days=-30):
        incidences = self._incidences.filter(
            police_date__range=(self._ref_date + timedelta(days=delta_days), self._ref_date))
        x_axis = ['DIA'.decode('UTF8'), 'NOCHE'.decode('UTF8')]
        y_axis = []
        for d in [range(9, 21), range(21, 24) + range(0, 9)]:
            y_axis.append(incidences.extra(
                where=['extract(hour from incidence_time) in (%s)' % ','.join(map(str, d))]).count())

        try:
            y_axis[0] = round((y_axis[0] * 100 / (y_axis[0] + y_axis[1])))
            y_axis[-1] = 100 - y_axis[0]
        except:
            y_axis[0] = 0
            y_axis[-1] = 0
        host, bucket, file_name = grafico_robos_dia(x_axis, y_axis)

        incidence_statistic = IncidenceStatisticImage.objects.create(province=self._province,
                                                                     type=IncidenceStatisticImage.DAY_AND_NIGHT_THEFTS,
                                                                     host=host,
                                                                     bucket=bucket,
                                                                     name=file_name)

        return incidence_statistic