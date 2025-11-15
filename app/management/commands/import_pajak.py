import json
from django.core.management.base import BaseCommand
from pajak.models import TransaksiPajak

class Command(BaseCommand):
    help = "Import data pajak dari JSON"

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **kwargs):
        with open(kwargs['file_path']) as f:
            data = json.load(f)

        for item in data:
            TransaksiPajak.objects.create(
                objek_nama=item['objek_nama'],
                npwpd=item['npwpd'],
                bulan=int(item['an']),
                tahun=int(item['transaksi_periodepajak']),
                omzet_makanan=item['transaksi_propertis']['omzetmakanan'],
                omzet_minuman=item['transaksi_propertis']['omzetminuman'],
                pajak=item['transaksi_jmlhpajak'],
                status_bayar=item['statusbayar'] == "1",
                tgl_bayar=item['tglbayar'],
                tgl_jatuh_tempo=item['tgljatuhtempo']
            )
