# -*- coding: utf-8 -*-

# This script is responsible for building the graph visualization

from pyvis.network import Network
import networkx as nx
import pickle, os, shutil

from makegraph import GraphResult, PageType

def loadInformation() -> GraphResult:
    with open('build/dependencies-graph.pickle', 'rb') as f:
        usesRelationsMap: dict[str, list[str]] = pickle.load(f)

    with open('build/pagetypes.pickle', 'rb') as f:
        pageTypes: dict[str, PageType] = pickle.load(f)

    return usesRelationsMap, pageTypes

def findUsedByRelations(usesRelationsMap: dict[str, list[str]]) -> dict[str, list[str]]:
    usedByRelationsMap: dict[str, list[str]] = {}

    for node, dependencies in usesRelationsMap.items():
        usedByRelationsMap[node] = []

    for node, dependencies in usesRelationsMap.items():
        for dep in dependencies:
            usedByRelationsMap[dep].append(node)

    return usedByRelationsMap

def findNodeLevels(usesRelationsMap: dict[str, list[str]], pageTypes: dict[str, PageType]) -> dict[str, int]:
    nodeLevels: dict[str, int] = {}

    def findLevel(node: str, visiting: set[str]) -> int:
        if node in nodeLevels:
            return nodeLevels[node]
        if node in visiting:
            raise ValueError(f"Cycle detected at node {node}: {' -> '.join(visiting)} -> {node}")

        visiting.add(node)
        try:
            if pageTypes[node] == "external":
                level = -1 # External modules
            elif len(usesRelationsMap[node]) == 0:
                level = 0 # Leaf nodes (no dependencies)
            else:
                level = max(findLevel(dep, visiting) for dep in usesRelationsMap[node]) + 1
            nodeLevels[node] = level
            return level
        finally:
            visiting.pop()

    for node in usesRelationsMap.keys():
        findLevel(node, set())

    return nodeLevels

def buildPyvisGraph():
    usesRelationsMap, pageTypes = loadInformation()

    usedByRelationsMap = findUsedByRelations(usesRelationsMap)

    nodeLevels: dict[str, int] = findNodeLevels(usesRelationsMap, pageTypes)

    # Build the graph

    dag = nx.DiGraph() # initialize the graph

    # Add nodes

    for node in usesRelationsMap.keys():
        group = (
                1 if pageTypes[node] == "data" else
                2 if pageTypes[node] == "external" else
                3 if pageTypes[node] == "code" else
                4 if pageTypes[node] == "test" else
                -1
                )
        typeName = (
                "Data" if pageTypes[node] == "data" else
                "External" if pageTypes[node] == "external" else
                "Code" if pageTypes[node] == "code" else
                "Test" if pageTypes[node] == "test" else
                ""
                )
        tooltip = f"Name: {node}"
        tooltip += "\nType: " + typeName
        tooltip += f"\nUses (Outdegree): {str(len(usesRelationsMap[node]))}"
        tooltip += f"\nUsed By (Indegree): {str(len(usedByRelationsMap[node]))}"
        tooltip += f"\nLevel: {nodeLevels[node]}"
        dag.add_node(node,
            label=node,
            value=len(usedByRelationsMap[node]),
            title=tooltip,
            group=group,
            level=nodeLevels[node],
        )

    # Add edges based on USES relation

    for node in usesRelationsMap.keys():
        for dep in usesRelationsMap[node]:
            dag.add_edge(node, dep)

    return dag

def moveLibToCorrectLocation():
    # Since pyvis generates a "lib" folder for its JS/CSS dependencies in the same directory as the script is run,
    # we need to move it to the correct location in "docs"
    if os.path.exists('lib'):
        if os.path.exists('docs/lib'):
            shutil.rmtree('docs/lib')
        shutil.move('lib', 'docs/lib')

def saveDefaultNetwork(dag: nx.DiGraph):
    net = Network(
        height="750px", width="100%", bgcolor="#222222", font_color="white",
        directed=True, neighborhood_highlight=True, select_menu=True, filter_menu=True,
    )
    net.barnes_hut(gravity=-5000, central_gravity=7, spring_length=200, spring_strength=0.05, damping=0.30)

    net.from_nx(dag)
    net.show_buttons()
    net.toggle_physics(True)

    net.show('docs/default.html', notebook=False)

    moveLibToCorrectLocation()

def saveHierarchicalNetwork(dag: nx.DiGraph):
    net = Network(
        height="750px", width="100%", bgcolor="#222222", font_color="white",
        directed=True, neighborhood_highlight=True, select_menu=True, filter_menu=True,
        layout=True, # enable hierarchical layout
    )

    net.from_nx(dag)
    net.show_buttons()
    net.hrepulsion(central_gravity=10, node_distance=300)

    net.show('docs/hierarchical.html', notebook=False)

    moveLibToCorrectLocation()

if __name__ == "__main__":
    dag = buildPyvisGraph()
    saveDefaultNetwork(dag)
    saveHierarchicalNetwork(dag)
