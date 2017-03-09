from .config import get_config


def get_record_config(record_code=None):
    config = get_config('RECORDS', key=record_code)
    return config


def get_record_label_dict(doubles=False):
    def _get_double_records():
        return [(index, record_dict.get('label')) for index, record_dict in config.items()
                if record_dict.get('doubles')]

    def _get_records():
        return [(index, record_dict.get('label')) for index, record_dict in config.items()]

    config = get_record_config()
    if config:
        return _get_double_records() if doubles else _get_records()
    return None
