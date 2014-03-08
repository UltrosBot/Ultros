__author__ = 'Gareth Coles'


class NotReadyError(Exception):
    pass


class AlreadyRegisteredError(Exception):
    pass


class UnknownStorageTypeError(Exception):
    pass


class OtherOwnershipError(Exception):
    pass
