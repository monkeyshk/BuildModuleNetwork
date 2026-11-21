# -*- coding: utf-8 -*-

# This script is responsible for building the graph using BFS and determining page types.

from typing import Literal, Optional

import requestpage, analyzepage, pickle, json, os

PageType = Literal['code'] | Literal['data'] | Literal['external'] | Literal['test']

# Filter to exclude pages from the graph
# This is based on the wiki's convention
# on sandbox modules, documentation pages, etc.
def filterPageName(page: str) -> bool:
    return page.find("Sandbox") < 0 and \
        page.find("sandbox") < 0 and \
        not page.endswith(".json") and \
        not "doc" in page.split("/")

def determinePageType(name: str, currentPageType: Optional[PageType]) -> PageType:
    dataKeywords = ["Data", "Aliases", "Datasheet", "i18n"]
    if any(name.endswith(word) for word in dataKeywords):
        return "data"
    elif name.endswith("testcases"):
        return "test"
    elif currentPageType:
        return currentPageType
    # assign default if not been assigned a type
    return "code"

GraphResult = tuple[dict[str, list[str]], dict[str, PageType]]

def makeGraph() -> GraphResult:
    # Define a list of starting pages for BFS. In this case, we request all module pages from API
    # and filter it using custom rules
    # 
    # This list can also be self-defined!
    # For example, using just ["Pet"], the BFS will give 88 modules!
    # If there are any pages that are not "dependency-linked" with existing starting pages,
    # append those items to the following list so that they can be BFS-ed
    startFromPages = requestpage.requestListOfAllPages(828, "Module:")
    startFromPages = list(filter(filterPageName, startFromPages))

    print(f"Number of starting pages: {len(startFromPages)}")

    # Fetch each page content: detect require(), mw.loadData(), loader.require(), and loader.loadData()
    # Using BFS, build dependencies graph
    queue: list[str] = []
    dependenciesGraph: dict[str, list[str]] = {}
    pageTypes: dict[str, PageType] = {}

    for pg in startFromPages:
        name = pg.replace("Module:", "")
        queue.append(name)

    while len(queue) > 0:
        name = queue.pop(0).strip()
        if not name in dependenciesGraph:
            print("Finding dependencies for", name)

            content = requestpage.makePageContentRequest("Module:" + name)
            if not content:
                print("Page not found")
                pageTypes[name] = "external"
                continue

            result = analyzepage.findDependencies(content)
            dependencies, dataDependencies = result
            dependencies = list(filter(filterPageName, dependencies))
            dataDependencies = list(filter(filterPageName, dataDependencies))

            combinedDependencies = dependencies + dataDependencies
            dependenciesGraph[name] = combinedDependencies
            queue += combinedDependencies

            print(combinedDependencies)

            # Assign page type to current page
            pageTypes[name] = determinePageType(
                name=name,
                currentPageType=pageTypes[name] if name in pageTypes else None,
            )

            # Assign data page type to all data dependencies
            for dataPage in dataDependencies:
                pageTypes[dataPage] = "data"

    print(dependenciesGraph)
    print(len(dependenciesGraph))

    return dependenciesGraph, pageTypes

def saveGraph(graphResult: GraphResult):
    dependenciesGraph, pageTypes = graphResult

    os.makedirs("build", exist_ok=True)

    with open("build/dependencies-graph.json", "w") as f:
        f.write(json.dumps(dependenciesGraph, indent=4))
        f.close()

    with open('build/dependencies-graph.pickle', 'wb') as f:
        pickle.dump(dependenciesGraph, f)

    with open("build/pagetypes.json", "w") as f:
        f.write(json.dumps(pageTypes, indent=4))
        f.close()

    with open('build/pagetypes.pickle', 'wb') as f:
        pickle.dump(pageTypes, f)

if __name__ == "__main__":
    graphResult = makeGraph()
    saveGraph(graphResult)
