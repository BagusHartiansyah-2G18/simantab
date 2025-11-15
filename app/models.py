from django.db import models
class TransaksiPajak(models.Model):
    bulan = models.CharField(max_length=2, null=True, blank=True)
    bulan_huruf = models.CharField(max_length=20, null=True, blank=True)
    tahun = models.IntegerField(null=True, blank=True)

    nopd = models.CharField(max_length=30, null=True, blank=True)
    npwpd = models.CharField(max_length=20, null=True, blank=True)
    wp_id = models.CharField(max_length=50, null=True, blank=True)

    objek_id = models.CharField(max_length=50, null=True, blank=True)
    objek_nama = models.CharField(max_length=100, null=True, blank=True)
    objek_alamat = models.TextField(null=True, blank=True)

    pengguna_nama = models.CharField(max_length=100, null=True, blank=True)
    subjenispajak_id = models.CharField(max_length=50, null=True, blank=True)
    subjenispajak_nama = models.CharField(max_length=100, null=True, blank=True)

    omzet_makanan = models.IntegerField(null=True, blank=True)
    omzet_minuman = models.IntegerField(null=True, blank=True)
    pajak = models.IntegerField(null=True, blank=True)
    status_bayar = models.BooleanField(null=True, blank=True)

    tgl_bayar = models.DateField(null=True, blank=True)
    tglbayar1 = models.DateTimeField(null=True, blank=True)
    tgl_entry = models.DateTimeField(null=True, blank=True)
    tgl_jatuh_tempo = models.DateField(null=True, blank=True)

    transaksi_jmlhbayardenda = models.IntegerField(null=True, blank=True)
    transaksi_jmlhdendapembayaran = models.IntegerField(null=True, blank=True)
    transaksi_kodebayarbank = models.CharField(max_length=50, null=True, blank=True)
    transaksi_kodeqris = models.TextField(null=True, blank=True)

    transaksi_masaawal = models.DateField(null=True, blank=True)
    transaksi_masaakhir = models.DateField(null=True, blank=True)
    transaksi_periodepajak = models.CharField(max_length=4, null=True, blank=True)

    transaksi_tglawalreklame = models.CharField(max_length=20, null=True, blank=True)
    transaksi_tglakhirreklame = models.CharField(max_length=20, null=True, blank=True)

    transaksi_propertis = models.JSONField(default=dict, null=True, blank=True)

    def rasio_pembayaran(self):
        total_omzet = (self.omzet_makanan or 0) + (self.omzet_minuman or 0)
        return self.pajak / total_omzet if total_omzet > 0 and self.pajak else 0


class SimtaxSession(models.Model):
    cookies = models.JSONField(default=dict)
    note = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)