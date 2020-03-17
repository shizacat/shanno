class FileParseException(Exception):
    """Occurs when parsing a file"""
    def __init__(self, msg="", line_num=-1):
        self.msg = msg
        self.line_num = line_num

    def __str__(self):
        return repr(self.msg)
