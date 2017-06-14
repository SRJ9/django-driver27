from operator import le, ge, eq
import re


class Streak(object):
    results = None
    max_streak = False

    def __init__(self, results, max_streak=False):
        self.results = results
        self.max_streak = max_streak

    @staticmethod
    def get_builtin_function(builtin_key):
        return {'lte': le,
                'gte': ge,
                'eq': eq,
                'exact': eq
                }.get(builtin_key, None)

    @staticmethod
    def validate_syntax_filter(current_filter):
        if not re.match(r'^(\w)+$', current_filter):
            raise Exception('Invalid streak filter syntax')

    @staticmethod
    def split_filter(curr_filter):
        split_char = '__'
        return curr_filter.split(split_char)

    @staticmethod
    def get_comparison_position(filter_list):
        return len(filter_list) - 1

    @classmethod
    def get_comparison_item(cls, filter_list):
        comparison_position = cls.get_comparison_position(filter_list)
        return filter_list[comparison_position]

    @classmethod
    def exists_comparison(cls, filter_list):
        comparison_position = cls.get_comparison_position(filter_list)
        return filter_list[comparison_position] in ['lte', 'gte', 'eq', 'exact']

    @classmethod
    def exec_comparison(cls, result, filter_list, filter_value):
        comparison_key = 'eq'
        if cls.exists_comparison(filter_list):
            comparison_key = cls.get_comparison_item(filter_list)
            filter_list.pop(cls.get_comparison_position(filter_list))
        filter_key = '.'.join(filter_list)
        result_attr = getattr(result, filter_key)
        builtin_function = cls.get_builtin_function(comparison_key)
        return builtin_function(result_attr, filter_value) if builtin_function else False

    @classmethod
    def checked_filters(cls, result, filters):
        passed_filter = True  # until is a false condition, filter is passed
        for curr_filter in filters:
            filter_value = filters[curr_filter]
            filter_list = cls.split_filter(curr_filter)
            comparison_result = cls.exec_comparison(result, filter_list, filter_value)
            if not comparison_result:
                passed_filter = False
                break
        return passed_filter

    def run(self, filters):
        count = 0
        max_count = 0
        for result in self.results:
            is_ok = self.checked_filters(result, filters)
            if not is_ok:
                if self.max_streak:
                    count = 0
                    continue
                else:
                    break
            count += 1
            if self.max_streak and count > max_count:
                max_count = count
        return max_count if self.max_streak else count
