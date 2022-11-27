
class UnsupportedOperationException(Exception):
    def __init__(self, *args: object) -> None:
        self.message = "Not allowed on sensitive value"
        super().__init__(self.message, *args)
    