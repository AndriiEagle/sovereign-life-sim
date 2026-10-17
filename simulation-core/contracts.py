"""Small shared boundary checks; generated code never runs in this module."""
import json
import math
import re


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def number(value, name, low, high, integer=False):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('INVALID_' + name)
    if integer and type(value) is not int:
        raise ValueError('INTEGER_REQUIRED_' + name)
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', value):
        raise ValueError('INVALID_ID')
    return value


def text(value, maximum=160):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise ValueError('INVALID_TEXT')
    if re.search(r'(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{15,}|-----BEGIN .*PRIVATE KEY)', value):
        raise ValueError('SECRET_LIKE_INPUT_REJECTED')
    return value.strip()


def keys(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError('INVALID_OBJECT_KEYS')
    return value
