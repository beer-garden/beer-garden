from mongoengine import QuerySet, QuerySetNoCache, fields


def _delete_file_field_objects(queryset):
    """Deletes the files for each item in the queryset"""
    file_field_names = []

    for name, field in queryset._document._fields.items():
        if isinstance(field, fields.FileField):
            file_field_names.append(name)

    if file_field_names:
        for item in queryset.all():
            for field_name in file_field_names:
                getattr(item, field_name).delete()


class FileFieldHandlingQuerySet(QuerySet):
    """A QuerySet that appropriately handles cleanup of any FileField fields (gridfs
    objects) when calling delete()"""

    def delete(self, *args, **kwargs):
        _delete_file_field_objects(self)
        super().delete(*args, **kwargs)

    def no_cache(self):
        """Convert to a non-caching queryset"""
        return self._clone_into(
            FileFieldHandlingQuerySetNoCache(self._document, self._collection)
        )


class FileFieldHandlingQuerySetNoCache(QuerySetNoCache):
    """A QuerySetNoCache that appropriately handles cleanup of any FileField fields
    (gridfs objects) when calling delete()"""

    def delete(self, *args, **kwargs):
        _delete_file_field_objects(self)
        super().delete(*args, **kwargs)
