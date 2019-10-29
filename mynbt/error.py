# ====================================================================
# Errors
# ====================================================================
class MyNBTError(Exception):
    """ Base class for all errors issued by MyNBT library
    """
    def __init__(self, message, **kwargs):
        super().__init__(message.format(**kwargs))

# ====================================================================
# Warnings
# ====================================================================
class MyNBTWarning(UserWarning):
    """ Base class for all warnings issued by MyNBT library
    """
    def __init__(self, message, **kwargs):
        super().__init__(message.format(**kwargs))
