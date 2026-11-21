# -*- coding: utf-8 -*-

# This script is responsible for analyzing a page, like finding dependencies.

import re

# require(...)
# loader.require(...)
# loader.lazy.require(...)
lineFormats = [
    r'(?<!\.)require\((.*?)\)',
    r'loader\.require\((.*?)\)',
    r'loader\.lazy\.require\((.*?)\)',
]

# mw.loadData(...)
# loader.loadData(...)
# loader.lazy.loadData(...)
dataLineFormats = [
    r'mw\.loadData\((.*?)\)',
    r'loader\.loadData\((.*?)\)',
    r'loader\.lazy\.loadData\((.*?)\)',
]

# "..."
# '...'
# [[...]]
importFormats = [
    r'"([^"]+)"',
    r"'([^']+)'",
    r"\[\[(.+)\]\]",
]

def uppercaseFirst(text: str) -> str:
    # Note: str.capitalize() would lowercase the remaining characters.
    return text[:1].upper() + text[1:]

# Convert required modules to standard names
def standardizePageName(name: str) -> str:
    name = name.replace("Module:", "").replace("module:", "").replace("_", " ").strip()
    return uppercaseFirst(name)

# Scan page and return all required modules
# Returns a tuple (normal_imports_detected, data_imports_detected)
def findDependencies(content: str) -> tuple[list[str], list[str]]:
    # Search for all require/loadData calls in the content
    callStrings: list[str] = []
    dataCallStrings: list[str] = []

    for line in content.split("\n"):
        is_comment = line.strip().startswith("--")
        if is_comment:
            continue

        for pattern in lineFormats:
            callStrings += re.findall(pattern, line)

        for pattern in dataLineFormats:
            dataCallStrings += re.findall(pattern, line)

    # Match the page names
    imports: list[str] = []
    for match in callStrings:
        for pattern in importFormats:
            imports += re.findall(pattern, match)

    dataImports: list[str] = []
    for match in dataCallStrings:
        for pattern in importFormats:
            dataImports += re.findall(pattern, match)

    # Return a list with all "Module:" removed, and then with all empty string removed
    return (
        [standardizePageName(name) for name in imports],
        [standardizePageName(name) for name in dataImports],
    )
