# coding=utf-8

"""
Logging handler that sends exceptions to the Ultros metrics service, if
enabled.
"""

__author__ = 'Gareth Coles'

from logbook.handlers import Handler


class MetricsHandler(Handler):
    """
    Simple handler for sending metrics to Ultros' metrics service.

    .

    .

    .

    .

    .

    Seriously, that's it. Were you expecting something else?
    """

    def __init__(self):
        super(MetricsHandler, self).__init__(bubble=True)

    def emit(self, record):
        """
        Send an exception from an error-level record to the metrics system.

        :type record: logbook.LogRecord
        :param record:
        :return:
        """

        try:
            if record.level_name.lower() == u"error":
                if record.exc_info is not None:
                    from system.metrics import Metrics

                    metrics = Metrics()
                    metrics.submit_exception(record.exc_info)
        except Exception as e:
            print("Error submitting exception: {}".format(e))
