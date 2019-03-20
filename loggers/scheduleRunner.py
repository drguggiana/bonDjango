from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from .views import dump_database

# see https://medium.com/@kevin.michael.horan/scheduling-tasks-in-django-with-the-advanced-python-scheduler-663f17e868e6
# for tutorial that got me here with the scheduling

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(dump_database, 'interval', weeks=1)
    scheduler.start()
