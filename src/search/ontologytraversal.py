from ..traverse.graph import graph

def search(edgesum, n, x, node, traversed):
    traversed.append(node)
    children = [x for x in graph.getNeighbors(node) if x not in traversed]
    print('\n')

    sv =  edgesum/(n*x)

    if children == [] or sv < 0.5:
        return (node, sv)
    else:
        for i in children:
            edgesum += graph.getNeighbors(node)[i]
            n += 1
            print((node, i, edgesum/(n*x)))
            search(edgesum, n, x, i, traversed)


if __name__ == "__main__":
    graph = graph()

    graph.addEdge('A', 'B', 0.1)
    graph.addEdge('B', 'D', 0.2)
    graph.addEdge('A', 'D', 0.4)
    graph.addEdge('A', 'C', 0.2)
    graph.addEdge('C', 'E', 0.3)

    print(search(1, 1, 1, 'A', []))
