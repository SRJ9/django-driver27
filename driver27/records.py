from .config import get_config


def get_record_config(record_code=None):
    config = get_config('RECORDS', key=record_code)
    return config


def get_record_label_dict():
    config = get_record_config()
    if config:
        return [(record_dict.get('label'), index) for index, record_dict in config.items()]
    return None
