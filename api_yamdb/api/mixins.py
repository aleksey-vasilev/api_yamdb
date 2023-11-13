from rest_framework import mixins, viewsets, filters

from .permissions import Admin, ReadOnly
from users.validators import validator_username


class UsernameVilidatorMixin:
    def validate_username(self, value):
        return validator_username(value)


class ObjectMixin(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    filter_backends = (filters.SearchFilter,)
    permission_classes = (Admin | ReadOnly,)
    search_fields = ('name',)
    lookup_field = 'slug'
