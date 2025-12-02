from app.models import TransaksiPajak

import pandas as pd

import re
from collections import defaultdict

import json


NORMALISASI_KECAMATAN = {
    "taliwang": ["taliwang", "tallingwang", "talingwang", "tliwang", "liwang"],
    "brang rea": ["brang rea", "brangrea", "brang re’a", "brang re'a", "brang re", "brangre"],
    "brang ene": ["brang ene", "brangene", "brang ene’", "brang ene'", "brangeneh"],
    "jereweh": ["jereweh", "jeroeh", "jreweh", "jerewe", "jerweh"],
    "maluk": ["maluk", "meluk", "malok", "maluak"],
    "seteluk": ["seteluk", "steluk", "sateluk", "setlk"],
    "poto tano": ["poto tano", "pototano", "poto-tano", "poto tanno", "pt tano"],
    "sekongkang": ["sekongkang"]
}

MAP_EJAAN = {}
for kecamatan, variants in NORMALISASI_KECAMATAN.items():
    for v in variants:
        MAP_EJAAN[v.lower()] = kecamatan.title()


def normalisasi_kecamatan(raw_name: str) -> str:
    """Normalisasi nama kecamatan dari string acak."""
    if not raw_name:
        return ""

    raw = raw_name.lower().strip()

    # Cocokkan langsung berdasarkan variant
    for salah, benar in MAP_EJAAN.items():
        if salah in raw:
            return benar

    return raw_name.title()  # fallback
    
def dataFrameToJson(df):
    data_json = df.to_dict(orient='records')  # list of dicts
    return json.dumps(data_json) 




class Dtransaksi:
    def __init__(self):
        data = TransaksiPajak.objects.all()
        if not data.exists():
            self.dt = pd.DataFrame()  # atau bisa set ke None, tergantung kebutuhan
        else:
            df = pd.DataFrame({'data': data}) 
            df['data_dict'] = df['data'].apply(lambda x: x.__dict__ if x is not None else {})
            self.dt = pd.json_normalize(df['data_dict'])
            self.dt['tgl_bayar'] = pd.to_datetime(self.dt['tgl_bayar'], errors='coerce') 
            self.dt['periode'] = self.dt['tgl_bayar'].dt.to_period('M')
        
    def periode(self):
        return self.dt['periode'].drop_duplicates()
    def jenisPAD(self):
        return (
            self.dt.groupby('subjenispajak_id').agg({
                'transaksi_jmlhbayardenda': 'sum',
                'objek_nama': 'first',
                'objek_alamat': 'first',
                'pengguna_nama':'first',
                'subjenispajak_nama':'first'
            }).reset_index()
            .rename(columns={'transaksi_jmlhbayardenda': 'pajak','subjenispajak_nama':'jenis'})
        )
    def filterByPeriode(periode):
        # '2025-10'
        return self.dt[self.dt['periode'] == periode]

    def pengusaha(self):
        # return self.dt.groupby('objek_id')['pajak'].sum().reset_index()
        return (
            self.dt.groupby('objek_id').agg({
                'transaksi_jmlhbayardenda': 'sum',
                'objek_nama': 'first',
                'objek_alamat': 'first',
                'pengguna_nama':'first',
                'subjenispajak_nama':'first'
            })
            .reset_index()
            .rename(columns={'transaksi_jmlhbayardenda': 'pajak'})
        )

        # grouped = self.dt.groupby('objek_id')['pajak'].sum().reset_index()
        # objek_info = self.dt[['objek_id']].drop_duplicates()
        # return pd.merge(grouped, objek_info, on='objek_id', how='left')
        
    def totalTransaksiPengusaha(self):
        # peruser = self.dt.groupby('objek_id')['berdenda'].sum().reset_index()
        # return (
        #     self.dt[self.dt['transaksi_jmlhdendapembayaran'] > 0]
        #     # self.dt
        #     .groupby('objek_id')
        #     .agg({
        #         'transaksi_jmlhdendapembayaran': 'count',
        #         'objek_nama': 'first',
        #         'objek_alamat': 'first',
        #         'pengguna_nama': 'first',
        #     })
        #     .reset_index()
        #     .rename(columns={'transaksi_jmlhdendapembayaran': 'transaksi_jmlhbayardenda'})
        # )

        return (
            self.dt.groupby('objek_id')
            .agg({
                # hitung hanya baris dengan nilai > 0
                'transaksi_jmlhdendapembayaran': lambda x: (x > 0).sum(),
                'objek_nama': 'first',
                'objek_alamat': 'first',
                'pengguna_nama': 'first',
            })
            .reset_index()
            .rename(columns={'transaksi_jmlhdendapembayaran': 'transaksi_jmlhbayardenda'})
        )

    def pengusahaBerdenda(self):
        # Hitung total denda per objek
        denda_objek = (
            self.dt.groupby('objek_id')['transaksi_jmlhdendapembayaran'].sum()
        )

        # Ambil hanya objek yang total dendanya > 0
        objek_tidak_taat = denda_objek[denda_objek > 0].index

        # Filter berdasarkan objek tersebut
        return (
            self.dt[self.dt['objek_id'].isin(objek_tidak_taat)]
            .groupby('objek_id')
            .agg({
                'transaksi_jmlhdendapembayaran': 'count',
                'objek_nama': 'first',
                'objek_alamat': 'first',
                'pengguna_nama': 'first',
            })
            .reset_index()
            .rename(columns={'transaksi_jmlhdendapembayaran': 'transaksi_jmlhbayardenda'})
        )

    def pengusahaTaat(self):
        # Hitung total denda per objek
        denda_objek = (
            self.dt.groupby('objek_id')['transaksi_jmlhdendapembayaran'].sum()
        )

        # Objek yang benar-benar 100% tanpa denda
        objek_taat = denda_objek[denda_objek == 0].index

        return (
            self.dt[self.dt['objek_id'].isin(objek_taat)]
            .groupby('objek_id')
            .agg({
                'transaksi_jmlhdendapembayaran': 'count',
                'objek_nama': 'first',
                'objek_alamat': 'first',
                'pengguna_nama': 'first',
            })
            .reset_index()
            .rename(columns={'transaksi_jmlhdendapembayaran': 'transaksi_jmlhbayardenda'})
        )

    
    def totalPajak(self):
        return self.dt['pajak'].sum()
    def totalOmzet(self):
        return (self.dt['omzet_makanan'].fillna(0) + self.dt['omzet_minuman'].fillna(0)).sum()

    def dataUpdate(self):
        last_update = self.dt.sort_values('tgl_bayar', ascending=False).head(1)
        return (
            last_update.iloc[0]['tgl_bayar'].strftime('%d %b %Y %H:%M')
            if not last_update.empty and pd.notnull(last_update.iloc[0]['tgl_bayar'])
            else "-"
        )
    def count(self):
        return len(self.dt)
    
    def daftarPajakPerbulan(self):
        hasil = self.dt.groupby('periode').agg({
            'pajak': 'sum',
            'transaksi_jmlhdendapembayaran': 'sum',
            'id': 'count'
        }).reset_index()
        hasil.rename(columns={
            'transaksi_jmlhdendapembayaran': 'denda',
            'id': 'jumlah_data'
        }, inplace=True)

        berdenda = self.dt
        berdenda['berdenda']=berdenda['transaksi_jmlhdendapembayaran'] > 0
        jumlah_berdenda = berdenda.groupby('periode')['berdenda'].sum().reset_index()
        hasil = hasil.merge(jumlah_berdenda, on='periode')
        hasil.rename(columns={'berdenda': 'jumlah_berdenda'}, inplace=True)
        return hasil

    def groupBykecamatan(self):
        hasil = defaultdict(lambda: {"total_objek": 0, "total_pajak": 0,"data": []})

        data = (
            self.dt.groupby('objek_id').agg({
                'transaksi_jmlhbayardenda': 'sum',
                'id': 'count',
                'objek_alamat':'first'
            }).reset_index()
            .rename(columns={'transaksi_jmlhbayardenda': 'pajak','id':'ttransaksi'})
        )

        for _, item in data.iterrows():
            alamat = item.get("objek_alamat", "")
            pajak = item.get("pajak", 0)
            kecamatan = ""

            # Ekstrak kecamatan via regex
            for bagian in alamat.split(","):
                bagian = bagian.strip().lower()
                match = re.search(r"(?:kecamatan|kec)\s+([a-zA-Z\s]+)", bagian, re.IGNORECASE)
                if match:
                    kecamatan = match.group(1).strip()
                    break

            # Normalisasi kecamatan
            kecamatan = normalisasi_kecamatan(kecamatan)

            if kecamatan:
                hasil[kecamatan]["total_objek"] += 1
                hasil[kecamatan]["total_pajak"] += pajak
                hasil[kecamatan]["data"].append(item.to_dict())

        return pd.DataFrame([
            {
                "periode": kec,
                "total_objek": val["total_objek"],
                "total_pajak": val["total_pajak"]
            }
            for kec, val in dict(hasil).items()
        ])
     
    def delAllTransaksi(self):
        TransaksiPajak.objects.all().delete()
