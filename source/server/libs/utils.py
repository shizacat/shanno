def is_int(s) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False
