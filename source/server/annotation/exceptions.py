class AnnotationBaseExcept(Exception):
    """Base exception"""
    def __init__(self, msg=""):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class FileParseException(AnnotationBaseExcept):
    """Occurs when parsing a file"""
    def __init__(self, msg="", line_num=-1):
        self.msg = msg
        self.line_num = line_num

    def __str__(self):
        return repr(self.msg)
