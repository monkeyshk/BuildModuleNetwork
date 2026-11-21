# -*- coding: utf-8 -*-

# This module is to support `makegraph.py`.

from typing import Optional

import requests, sys

# Perform get request for the page list for one time
def makePageListRequest(apcontinue: str, apnamespace: int) -> list[str]:
    payload = {
        "action": "query",
        "format": "json",
        "list": "allpages",
        "apfilterredir": "nonredirects",
        "aplimit": "1000",
        "apcontinue": apcontinue,
        "apnamespace": apnamespace,
        "maxlag": 5,
    }
    try:
        resp = requests.get("https://hypixelskyblock.minecraft.wiki/api.php", params=payload)
        data = resp.json()
        pageList: list[str] = [page["title"] for page in data["query"]["allpages"]]
    except Exception as e:
        print("Errored in requesting list from page: " + apcontinue)
        print(e)
        print("Exiting")
        sys.exit()

    return pageList

# Make as many requests as needed to get a list of all pages in namespace
def requestListOfAllPages(namesapceId: int, namespaceStr: str = "") -> list[str]:
    apcontinue = ""
    tempList = makePageListRequest("", namesapceId)
    pageList = tempList.copy()
    while (len(tempList) > 1):
        apcontinue = tempList[-1].replace(" ", "_").replace(namespaceStr, "")
        tempList = makePageListRequest(apcontinue, namesapceId)
        pageList += tempList
    pageList = [page.replace("Module:", "") for page in set(pageList)]
    pageList.sort()
    return pageList

# Perform get request for a page
# Returns the page content (None if not found)
def makePageContentRequest(page: str) -> Optional[str]:
    payload = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": page.replace(" ", "_"),
        "formatversion": 2,
        "rvprop": "content",
        "rvslots": "*",
        "maxlag": 5,
    }
    try:
        resp = requests.get("https://hypixelskyblock.minecraft.wiki/api.php", params=payload)
        data = resp.json()
        if "missing" in data["query"]["pages"][0]:
            return None
        else:
            content: str = data["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
            return content
    except Exception as e:
        print("Errored in requesting page: " + page)
        print(e)
        print("Exiting")
        sys.exit()
