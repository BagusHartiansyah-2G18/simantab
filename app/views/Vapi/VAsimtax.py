import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from app.models import SimtaxSession,TransaksiPajak
from requests.utils import dict_from_cookiejar, cookiejar_from_dict

import base64
from datetime import datetime
import pytz
import hashlib
from urllib.parse import urlparse

from app.views.Vapi.serializers import TransaksiPajakSerializer
from rest_framework import viewsets

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action


SIMTAX_BASE = "https://simtax.sumbawabaratkab.go.id/web"
SIMTAX_API_BASE = "https://api-simtax.sumbawabaratkab.go.id/"

def basic():
    tz = pytz.timezone("Asia/Jakarta")
    tanggal = datetime.now(tz).strftime("%Y%m%d")
    
    # Hash dengan MD5 seperti De.init(...)
    raw_password = tanggal + "$DM99issumbbrtNK2023$"
    hashed_password = hashlib.md5(raw_password.encode()).hexdigest()

    username = "simpatdasumbawabarat"
    credentials = f"{username}:{hashed_password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    return f"Basic {encoded_credentials}"



@csrf_exempt
def simtax_login(request):
    sess = requests.Session()

    username = "197210172007011014"
    password = "12131415" 

    files = {
        "username": (None,username),
        "password": (None,password),
    }
 

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": basic(),
        # "Authorization": "Basic c2ltcGF0ZGFzdW1iYXdhYmFyYXQ6MWYyMzVmYjZlMGRkZGEzYjNiNzZlY2E3NzUzNGM2YWY="
    }
    r = sess.post(
        SIMTAX_API_BASE+"admin/login",
        headers=headers,
        files=files,
    )

    try:
        data = r.json()
    except:
        data = r.text

    # token disimpan di Django session
    request.session["simtax_token"] = data.get("accessToken")
    request.session["simtax_sinkron"] = True
    return JsonResponse({
        "status": r.status_code,
        "response": data,
    })

@csrf_exempt
def simtax_get_transaksi(request):
    token = request.session.get("simtax_token")
    if not token:
        simtax_login(request)
        return JsonResponse({"error": "Not logged in"}, status=401)

    nextProses = request.session.get("simtax_sinkron")
    if nextProses is False:
        print(nextProses)
        return JsonResponse({
            "response": {"success": True,"mgs":"up to date!!!"},
        })
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0",
    }

    # base_url = SIMTAX_API_BASE+"backoffice/laporan/transaksi?
    # start=0&length=10&keyword=&tglawal=2025-01-01&tglakhir=2025-12-31
    # &subjenispajak_id=7D8C02E255FA9166869614AB7899D496&objek_nama=&objek_id=&wp_id=&kode_bayar="

    # parsed = urlparse(base_url)
    # url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # url = (
    #     SIMTAX_API_BASE+"backoffice/transaksi"
    #     +"?start=0&length=10&keyword=&tglawal=2025-01-01&tglakhir=2025-12-31"
    #     +"&subjenispajak_id=7D8C02E255FA9166869614AB7899D496"
    #     +"&objek_nama=&objek_id=&wp_id=&kode_bayar="
    # )

    start = TransaksiPajak.objects.count()
    endpoint = "backoffice/laporan/transaksi"

    params = {
        "start": start,
        "length": 100,
        "keyword": "",
        "tglawal": "2025-01-01",
        "tglakhir": "2025-12-31",
        "subjenispajak_id": "7D8C02E255FA9166869614AB7899D496",
        "objek_nama": "",
        "objek_id": "",
        "wp_id": "",
        "kode_bayar": ""
    }
    url = SIMTAX_API_BASE + endpoint
    try:
        r = requests.get(url,params=params, headers=headers)
    except Exception as e:
        return JsonResponse({"error": "request_failed", "detail": str(e)}, status=500)

    try:
        data = r.json()
    except:
        data = r.text

    # print("Tipe data:", type(data))
    if isinstance(data, dict):
    # if 0:
        items = data.get('data')
        if items and isinstance(items, list):
            objects = []
            for item in items:
                obj = TransaksiPajak(
                    bulan=item['bulan'],
                    bulan_huruf=item['bulan_huruf'],
                    tahun=int(item['transaksi_periodepajak']),
                    nopd=item['nopd'].strip(),
                    npwpd=item['npwpd'],
                    wp_id=item['wp_id'],
                    objek_id=item['objek_id'],
                    objek_nama=item['objek_nama'],
                    objek_alamat=item['objek_alamat'],
                    pengguna_nama=item['pengguna_nama'],
                    subjenispajak_id=item['subjenispajak_id'],
                    subjenispajak_nama=item['subjenispajak_nama'],
                    omzet_makanan=safe_number(item['transaksi_propertis']['omzetmakanan']),
                    omzet_minuman=safe_number(item['transaksi_propertis']['omzetminuman']),
                    pajak=item['transaksi_jmlhpajak'],
                    status_bayar=(item['statusbayar'] == '1'),
                    tgl_bayar=datetime.strptime(item['tglbayar'], "%Y-%m-%d").date() if item['tglbayar'] else None,
                    tglbayar1=datetime.strptime(item['tglbayar1'], "%Y-%m-%d %H:%M:%S") if item['tglbayar1'] else None,
                    tgl_entry=datetime.strptime(item['tglentry'], "%Y-%m-%dT%H:%M:%S.%fZ") if item['tglentry'] else None,
                    tgl_jatuh_tempo=datetime.strptime(item['tgljatuhtempo'], "%Y-%m-%d").date() if item['tgljatuhtempo'] else None,
                    transaksi_jmlhbayardenda=item['transaksi_jmlhbayardenda'],
                    transaksi_jmlhdendapembayaran=item['transaksi_jmlhdendapembayaran'],
                    transaksi_kodebayarbank=item['transaksi_kodebayarbank'],
                    transaksi_kodeqris=item['transaksi_kodeqris'],
                    transaksi_masaawal=datetime.strptime(item['transaksi_masaawal'], "%Y-%m-%d").date(),
                    transaksi_masaakhir=datetime.strptime(item['transaksi_masaakhir'], "%Y-%m-%d").date(),
                    transaksi_periodepajak=item['transaksi_periodepajak'],
                    transaksi_tglawalreklame=item['transaksi_tglawalreklame'],
                    transaksi_tglakhirreklame=item['transaksi_tglakhirreklame'],
                    transaksi_propertis=item['transaksi_propertis']
                )
                objects.append(obj)    
                
            TransaksiPajak.objects.bulk_create(objects)
            print("sukses menambahkan data baru!!!")
            if(int(data.get('totaldata', 0)) == (start + 100)):
                request.session["simtax_sinkron"] = False
        else:
            request.session["simtax_sinkron"] = False
            print("Key 'data' tidak ditemukan atau bukan list")

    
    return JsonResponse({
        "status": r.status_code,
        "url_used": url,        
        # "headers_sent": headers,
        "response": {"success": True},
        # "response": data,
    })



def simtax_get_pengguna(request):
    token = request.session.get("simtax_token")
    if not token:
        return JsonResponse({"error": "Not logged in"}, status=401)

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0",
    }

    # endpoint API SIMTAX untuk pencarian
    url = (
        "https://api-simtax.sumbawabaratkab.go.id/backoffice/transaksi"
        "?start=0&length=1000&keyword=&tglawal=2025-01-01&tglakhir=2025-12-31"
        "&subjenispajak_id=7D8C02E255FA9166869614AB7899D496"
        "&objek_nama=&objek_id=&wp_id=&kode_bayar="
    )
    # "https://api-simtax.sumbawabaratkab.go.id/backoffice/transaksi"
    #     "?start=0&length=500&keyword=&tglawal=2025-01-01&tglakhir=2025-12-31"
    #     "&subjenispajak_id=7D8C02E255FA9166869614AB7899D496&objek_nama=&objek_id=&wp_id=&kode_bayar="
        
    try:
        r = requests.get(url, headers=headers)
    except Exception as e:
        return JsonResponse({"error": "request_failed", "detail": str(e)}, status=500)

    try:
        data = r.json()
    except:
        data = r.text

    return JsonResponse({
        "status": r.status_code,
        "url_used": url,         # dipakai untuk debug
        "headers_sent": headers, # opsional
        "response": data,
    })

def safe_number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class TransaksiPajakViewSet(viewsets.ModelViewSet):
    queryset = TransaksiPajak.objects.all()
    serializer_class = TransaksiPajakSerializer
    # def list(self, request):
    #     queryset = self.get_queryset()
    #     serializer = self.get_serializer(queryset, many=True)

    #     # Print ke console untuk debugging
    #     print("Jumlah data:", queryset.count())
    #     for obj in queryset[:5]:  # batasi agar tidak overload
    #         print(obj.objek_nama, obj.pajak)

    #     return Response(serializer.data)

    @action(detail=False, methods=['get','delete'])
    def delete_all(self, request):
        count = TransaksiPajak.objects.count()
        TransaksiPajak.objects.all().delete()
        return Response({'message': f'{count} data dihapus.'})

    

