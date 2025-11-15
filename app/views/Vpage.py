from django.shortcuts import render
from app.models import TransaksiPajak
from django.contrib.auth.decorators import login_required

import pandas as pd
import matplotlib.pyplot as plt
import io
import urllib, base64
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot

import re
from collections import defaultdict

from app.views.sf.SFdata import Dtransaksi,dataFrameToJson

# mobil_saya = Mobil("Toyota", "Merah")
# mobil_saya.info()  # 

_ = Dtransaksi()

@login_required
def dashboard(request): 
    datax = _.daftarPajakPerbulan()
    config_pajak = {
        'kolom1': 'pajak',
        'kolom2': 'jumlah_data',
        'label1': 'Pajak',
        'label2': 'Jumlah Transaksi',
        'judul': 'Grafik Pajak dan Jumlah Transaksi per Bulan',
        'warna1': 'sunset',         # ✅ valid skema warna
        'warna2': 'Oranges'        # ✅ valid skema warna
    }

    config_denda = {
        'kolom1': 'denda',
        'kolom2': 'jumlah_berdenda',
        'label1': 'Denda',
        'label2': 'Pengusaha',
        'judul': 'Grafik Denda dan Jumlah Berdenda per Bulan',
        'warna1': 'Reds',          # ✅ valid skema warna
        'warna2': 'Greens'         # ✅ valid skema warna
    }



    chart_pajak = grafik_plotly_express_duo(datax, config_pajak)
    chart_denda = grafik_plotly_express_duo(datax, config_denda)

    
    hasil = _.groupBykecamatan()
    configKec = {
        "kolom1": "total_objek",
        "kolom2": "total_pajak",
        "label1": "Jumlah Objek",
        "label2": "Pajak",
        "judul": "Jumlah Objek & Pajak per Kecamatan",
        "warna1": "icefire"
    }

    grafik_kec = grafik_plotly_express_duo(hasil, configKec)
    tot =  _.pengusaha()
    context = {
        'chart_pajak': chart_pajak,
        'chart_denda': chart_denda,
        'grafik_kec':grafik_kec,
        'total_pajak':"{:,.0f}".format(_.totalPajak()),
        'total_omzet': "{:,.0f}".format(_.totalOmzet()),
        'tobjek': "{:,.0f}".format(len(tot)),
        'ttransaksi': "{:,.0f}".format(_.count()),
        "tgl":_.dataUpdate,
    }
    return render(request, 'dashboard.html', context)

@login_required
def user(request):
    data = TransaksiPajak.objects.all()
    total_pajak = sum([d.pajak for d in data])
    total_omzet = sum([d.omzet_makanan + d.omzet_minuman for d in data])
    rasio = total_pajak / total_omzet if total_omzet else 0
    # print(user)
    return render(request, "user.html", {
        "total_pajak": total_pajak,
        "rasio": f"{rasio:.2%}",
        "data": data
    })

@login_required
def data(request):
    context = {
        # 'data': data,
    }
    return render(request, 'Ddata.html', context)

@login_required
def pengusaha(request):
    data = dataFrameToJson(_.pengusaha())
    context = {
        'data': data,
    }
    return render(request, 'Dpengusaha.html', context)

@login_required
def wilaya(request):
    data = dataFrameToJson(_.groupBykecamatan())
    context = {
        'data': data,
    }
    return render(request, 'Dwilaya.html', context)

@login_required
def denda(request):
    data = dataFrameToJson(_.pengusahaBerdenda())
    context = {
        'data': data,
    }
    return render(request, 'Ddenda.html', context)


# batas 
def grafik_plotly_express_duo(df, config):
    """
    df: DataFrame dengan kolom 'periode', kolom1, kolom2
    config: dict dengan key:
        - 'kolom1': nama kolom utama (nilai batang)
        - 'kolom2': nama kolom label tambahan
        - 'label1': label untuk kolom utama
        - 'label2': label untuk label tambahan
        - 'judul': judul grafik
        - 'warna1': skema warna batang
    """
    df['periode'] = df['periode'].astype(str)

    # Format label tambahan
    df['label_text'] = df[config['kolom2']].apply(lambda v: f"{v:,} {config['label2']}")

    fig = px.bar(
        df,
        x='periode',
        y=config['kolom1'],
        title=config['judul'],
        labels={'periode': 'Periode', config['kolom1']: config['label1']},
        text='label_text',
        color=config['kolom1'],
        color_continuous_scale=config.get('warna1', 'Blues')
    )

    fig.update_traces(textposition='outside', texttemplate='%{text}')
    fig.update_layout(xaxis_tickangle=-45)

    return plot(fig, output_type='div')