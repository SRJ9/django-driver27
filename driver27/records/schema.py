from jsonmodels import models, fields, errors, validators
from django.utils.translation import ugettext as _


class RecordFilterSchema(models.Base):
    code = fields.StringField(required=True)
    label = fields.StringField(required=True)
    rec_filter = fields.EmbeddedField(dict, required=True)
    team_doubles_filter = fields.BoolField(required=False)


class RecordFilterList(object):

    filters = []

    def __init__(self, record_list):
        if not isinstance(record_list, list):
            raise Exception(_('Record list is not a list'))

        for x in record_list:
            self.validate(x)
            self.filters.append(x)

    def get_codes(self):
        return [x.code for x in self.filters]

    def filter_code(self, code):
        return [x for x in self.filters if x.code == code]

    def exists_code(self, code):
        return True if self.filter_code(code) else False

    def get_code(self, code):
        filter_code = self.filter_code(code=code)
        return filter_code[0] if len(filter_code) else None

    def validate(self, obj):
        if not isinstance(obj, RecordFilterSchema):
            raise Exception(_('Invalid record filter'))
        if self.exists_code(obj):
            raise Exception(_('%(code)s is duplicate record filter' % {'code': obj.code}))
        obj.validate()
        return True



