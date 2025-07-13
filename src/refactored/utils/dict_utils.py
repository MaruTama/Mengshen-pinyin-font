# -*- coding: utf-8 -*-
# !/usr/bin/env python

"""
Dictionary manipulation utilities.

Contains functions for working with nested dictionaries and data structures.
"""

from __future__ import annotations

from typing import Any, Dict, List


def deep_update(dict_base: Dict[str, Any], other: Dict[str, Any]) -> None:
    """
    Update nested dictionary structure recursively.

    [階層構造のあるdictをupdateする](https://www.greptips.com/posts/1242/)

    Args:
        dict_base: Base dictionary to update
        other: Dictionary with updates to apply
    """
    for k, v in other.items():
        if isinstance(v, dict) and k in dict_base:
            deep_update(dict_base[k], v)
        else:
            dict_base[k] = v


def safe_get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Safely get value from nested dictionary using key path.

    Args:
        data: Dictionary to search
        keys: List of keys forming the path (e.g., ['glyf', 'cid123', 'advanceWidth'])
        default: Default value if path not found

    Returns:
        Value at the specified path, or default if not found
    """
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def safe_set_nested(data: Dict[str, Any], keys: List[str], value: Any) -> None:
    """
    Safely set value in nested dictionary using key path.

    Creates intermediate dictionaries as needed.

    Args:
        data: Dictionary to modify
        keys: List of keys forming the path
        value: Value to set
    """
    current = data

    # Navigate to the parent of the target location
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            # If existing value is not a dict, overwrite it
            current[key] = {}
        current = current[key]

    # Set the final value
    if keys:
        current[keys[-1]] = value


def flatten_dict(
    data: Dict[str, Any], parent_key: str = "", separator: str = "."
) -> Dict[str, Any]:
    """
    Flatten nested dictionary structure.

    Args:
        data: Dictionary to flatten
        parent_key: Parent key prefix
        separator: Separator for flattened keys

    Returns:
        Flattened dictionary
    """
    items = []

    for k, v in data.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, separator).items())
        else:
            items.append((new_key, v))

    return dict(items)


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries with deep merging.

    Later dictionaries take precedence over earlier ones.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result = {}

    for d in dicts:
        deep_update(result, d)

    return result


def filter_dict_by_keys(
    data: Dict[str, Any], allowed_keys: List[str]
) -> Dict[str, Any]:
    """
    Filter dictionary to only include specified keys.

    Args:
        data: Dictionary to filter
        allowed_keys: List of keys to keep

    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in data.items() if k in allowed_keys}


def exclude_dict_keys(data: Dict[str, Any], excluded_keys: List[str]) -> Dict[str, Any]:
    """
    Filter dictionary to exclude specified keys.

    Args:
        data: Dictionary to filter
        excluded_keys: List of keys to exclude

    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in data.items() if k not in excluded_keys}
