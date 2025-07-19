from django import template
from urllib.parse import urlencode
from django.http import QueryDict

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')

@register.filter
def getattribute(obj, attr):
    return getattr(obj, attr, '')

@register.simple_tag
def url_replace(request, field, value):
    """
    Replace a parameter in the current URL with a new value
    """
    query_dict = request.GET.copy()
    query_dict[field] = value
    return query_dict.urlencode()
