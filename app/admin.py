from django.contrib import admin
from .models import TransaksiPajak

@admin.register(TransaksiPajak)
class TransaksiPajakAdmin(admin.ModelAdmin):
    list_display = ['objek_nama', 'npwpd', 'bulan', 'tahun', 'pajak', 'status_bayar']
    search_fields = ['objek_nama', 'npwpd']
    list_filter = ['tahun', 'status_bayar']
