def lr_diff(l, r):
    return list(set(l).difference(r))


def lr_intr(l, r):
    return list(set(l).intersection(r))


def season_bulk_copy(cls, cls_to_save, pks, pks_name, season_pk):
    items = cls.objects.filter(pk__in=pks)
    for item in items:
        item_filter = {pks_name: item}
        cls_to_save.objects.create(
            season_id=season_pk,
            **item_filter
        )