from json import JSONEncoder
from datetime import date

from person import Person


class PersonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Person):
            return o.last_name


class DateEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()
