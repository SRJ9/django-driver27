from .config import get_config


def get_record_config(record_code=None):
    config = get_config('RECORDS', key=record_code)
    return config


def get_record_label_dict(doubles=False):
    config = get_record_config()
    if config:
        if doubles:
            return [(record_dict.get('label'), index) for index, record_dict in config.items()
                    if record_dict.get('doubles')]
        else:
            return [(record_dict.get('label'), index) for index, record_dict in config.items()]
    return None
