from django.apps import AppConfig


class LoggersConfig(AppConfig):
    name = 'loggers'

    # override of the ready class to start the scheduler upon server startup
    def ready(self):
        from . import scheduleRunner
        scheduleRunner.start()
