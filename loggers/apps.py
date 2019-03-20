from django.apps import AppConfig


class LoggersConfig(AppConfig):
    name = 'loggers'

    def ready(self):
        from . import scheduleRunner
        scheduleRunner.start()
