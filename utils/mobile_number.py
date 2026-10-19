"""Normalize international mobile identifiers without guessing a country code."""
import re

MOBILE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_mobile(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError("Mobile number must use international format, such as +97312345678")
    normalized = re.sub(r"[\s()-]", "", value)
    if not MOBILE_PATTERN.fullmatch(normalized):
        raise ValueError("Mobile number must use international format, such as +97312345678")
    return normalized
