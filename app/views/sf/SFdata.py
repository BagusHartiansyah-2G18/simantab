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
    "poto tano": ["poto tano", "pototano", "poto-tano", "poto tanno", "pt tano"]
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
        df = pd.DataFrame({'data': data}) 
        df['data_dict'] = df['data'].apply(lambda x: x.__dict__ if x is not None else {})
        self.dt = pd.json_normalize(df['data_dict'])
        self.dt['tgl_bayar'] = pd.to_datetime(self.dt['tgl_bayar'], errors='coerce')
        self.dt['periode'] = self.dt['tgl_bayar'].dt.to_period('M')
        
    def periode(self):
        return self.dt['periode'].drop_duplicates()
    def filterByPeriode(periode):
        # '2025-10'
        return self.dt[self.dt['periode'] == periode]

    def pengusaha(self):
        # return self.dt.groupby('objek_id')['pajak'].sum().reset_index()
        return self.dt.groupby('objek_id').agg({
            'pajak': 'sum',
            'objek_nama': 'first',
            'objek_alamat': 'first',
            'pengguna_nama':'first',
        }).reset_index()

        # grouped = self.dt.groupby('objek_id')['pajak'].sum().reset_index()
        # objek_info = self.dt[['objek_id']].drop_duplicates()
        # return pd.merge(grouped, objek_info, on='objek_id', how='left')
        
    def pengusahaBerdenda(self):
        # peruser = self.dt.groupby('objek_id')['berdenda'].sum().reset_index()
        peruser = self.dt.groupby('objek_id').agg({
            'transaksi_jmlhbayardenda': 'count',
            'objek_nama': 'first',
            'objek_alamat': 'first',
            'pengguna_nama':'first',
        }).reset_index()
        return peruser[peruser['transaksi_jmlhbayardenda'] > 0]
    
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

        for _, item in self.dt.iterrows():
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
     
