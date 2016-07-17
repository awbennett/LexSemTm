"""
Created by: Andrew Bennett
Last updated: July, 2016

Provides custom exceptions
"""

class ExperimentFail(Exception):
    """
    exception for experiment failure
    """
    def __init__(self, message):
        Exception.__init__(self, message)


class WSIRepeat(Exception):
    """
    exceptions indicating that experiment needs to be repeated
    """
    def __init__(self, message):
        Exception.__init__(self, message)
