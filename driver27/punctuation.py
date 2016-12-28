from .config import get_config


def get_punctuation_config(punctuation_code=None):
    config = get_config('PUNCTUATION', key=punctuation_code)
    return config


def get_punctuation_label_dict():
    config = get_punctuation_config()
    if config:
        return [(punctuation_dict.get('label'), index) for index, punctuation_dict in config.items()]
    return None
