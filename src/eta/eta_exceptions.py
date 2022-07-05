class EndOfService(Exception): pass

class APIError(Exception): pass

class EmptyDataError(Exception): pass

class StationClosed(Exception): pass

class AbnormalService(Exception): pass
    
# class EmptyDataError(Exception):

#     def __init__(self, *args: object, message: str = "", details: str = "none") -> None:
#         super().__init__(*args)

#     def __str__(self) -> str:
#         return super().__str__()