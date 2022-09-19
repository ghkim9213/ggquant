class FsDetailNotFoundError(Exception):
    def __init__(self, fa):
        msg = f"FsDetail for {fa} not found"
        super.__init__(msg)
