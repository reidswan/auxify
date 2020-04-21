from datetime import datetime
from rapidjson import dumps
from typing import Dict, Any

ISO_FORMAT='%Y-%m-%dT%H:%M:%S.%f'

def serialize_datetime(dt: datetime)-> str:
    return dt.isoformat()

def deserialize_datetime(dt: str)-> datetime:
    return datetime.strptime(dt, ISO_FORMAT)


def _encode_default(data: Any)-> str:
    if isinstance(data, datetime):
        return data.isoformat()
    return str(data)


def json_dumps_with_default(data: Dict, *a, **k)-> str:
    return dumps(data, *a, **k, default=_encode_default)
