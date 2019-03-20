from datetime import datetime # necessary import, do not delete
from apscheduler.schedulers.background import BackgroundScheduler
from .views import dump_database

# see https://medium.com/@kevin.michael.horan/scheduling-tasks-in-django-with-the-advanced-python-scheduler-663f17e868e6
# for tutorial that got me here with the scheduling


# start function for the scheduler, actually setting up the scheduler, assigning the interval and the function to run
def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(dump_database, 'interval', weeks=1)
    scheduler.start()
