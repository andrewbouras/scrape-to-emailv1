import schedule
import time
from generate import fetch_and_store_gi_studies

schedule.every().day.at("00:00").do(fetch_and_store_gi_studies)

while True:
    schedule.run_pending()
    time.sleep(60)