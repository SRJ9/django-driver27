# from .classes import RecordFilter
from .filters import DR27_RECORD_FILTERS
from .schema import RecordFilterSchema, RecordFilterList

DR27_RECORDS = RecordFilterList([RecordFilterSchema(**x) for x in DR27_RECORD_FILTERS])
