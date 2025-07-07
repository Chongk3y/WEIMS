from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')

@register.filter
def getattribute(obj, attr):
    return getattr(obj, attr, '')
