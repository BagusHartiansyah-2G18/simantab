import requests
from app.models import TransaksiPajak

def tarik_data_simtax():
    print("Menjalankan penarikan data SIMTAX...")
    start = 0
    length = 100

    while True:
        params = {"start": start, "length": length}
        headers = {"Authorization": "Bearer ..."}
        url = "https://simtax.local/api/data"

        r = requests.get(url, params=params, headers=headers)
        data = r.json().get("data", [])

        if not data:
            break

        for item in data:
            TransaksiPajak.objects.create(**item)  # sesuaikan field-nya

        start += length
