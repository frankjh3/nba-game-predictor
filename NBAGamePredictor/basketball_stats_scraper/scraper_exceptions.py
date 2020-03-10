class Error(Exception):
    pass


class InvalidStatType(Error):
    msg = 'InvalidStatType Error - Acceptable stat_types are:'
    print(msg)
