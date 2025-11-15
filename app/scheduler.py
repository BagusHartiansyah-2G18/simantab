from apscheduler.schedulers.background import BackgroundScheduler
from app.jobs import tarik_data_simtax

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(tarik_data_simtax, 'interval', minutes=30)
    scheduler.start()
