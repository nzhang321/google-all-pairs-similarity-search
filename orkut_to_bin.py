import os
import struct
from array import array
import time

IN_FILENAME = "com-orkut.ungraph.txt"
OUT_FILENAME = "orkut_data.bin"

def orkut_to_bin(input_txt_path, output_bin_path, show_progress=True):
    """
    Convert an edge-list text file to the binary format expected by the
    All-Pairs C program. The output contains for each node (in order of
    non‑decreasing degree):
        - node ID (4 bytes, unsigned int)
        - degree (4 bytes, unsigned int)
        - neighbor IDs (4 bytes each, sorted increasingly)

    The implementation uses only ~1 GB of RAM for a graph of Orkut's size.
    """
    # ------------------------------------------------------------------
    # First pass: read the graph to obtain:
    #   - maximum node ID
    #   - degree of every node (both directions)
    # ------------------------------------------------------------------
    print("Pass 1: Counting degrees and finding max node ID...")
    deg = array('I')          # unsigned int, index = node ID
    max_node_id = 0
    line_count = 0

    with open(input_txt_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            u = int(parts[0])
            v = int(parts[1])

            # update max id
            if u > max_node_id:
                max_node_id = u
            if v > max_node_id:
                max_node_id = v

            # ensure deg array is long enough
            while len(deg) <= max_node_id:
                deg.append(0)

            # count both directions
            deg[u] += 1
            deg[v] += 1
            line_count += 1

    # deg[0] is unused (node IDs start at 1)
    print(f"   Found {line_count} undirected edges. Max node ID: {max_node_id}")

    # total number of directed neighbor entries
    total_neighbors = sum(deg)
    print(f"   Total directed edges (both directions): {total_neighbors}")

    # ------------------------------------------------------------------
    # Allocate the big neighbor array and compute prefix offsets.
    # ------------------------------------------------------------------
    print("Pass 2: Building CSR structure...")
    # offsets[node] = start index of node's neighbors in nbrs array
    # offsets[node+1] = end index (exclusive)
    offsets = array('Q', [0]) * (max_node_id + 2)   # unsigned long long

    for node in range(1, max_node_id + 1):
        offsets[node + 1] = offsets[node] + deg[node]

    # nbrs holds all neighbor entries, placed contiguously
    nbrs = array('I', [0]) * total_neighbors

    # pos is a working copy of offsets for filling
    pos = array('Q', offsets)

    # Second pass over the input file: fill the neighbor array
    with open(input_txt_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            u = int(parts[0])
            v = int(parts[1])

            # store v in u's list
            nbrs[pos[u]] = v
            pos[u] += 1
            # store u in v's list
            nbrs[pos[v]] = u
            pos[v] += 1

    # ------------------------------------------------------------------
    # Sort each node's neighbor list (required by the C program).
    # ------------------------------------------------------------------
    print("Sorting neighbor lists (by node degree order)...")
    total_nodes = max_node_id
    nodes_with_degree = [node for node in range(1, max_node_id + 1) if deg[node] > 0]
    # Sort nodes by degree so that we output vectors in non‑decreasing size
    nodes_sorted = sorted(nodes_with_degree, key=lambda n: deg[n])

    # We'll sort the neighbor lists in the same order to keep memory locality
    for idx, node in enumerate(nodes_sorted):
        if show_progress and (idx % 10000 == 0 or idx == len(nodes_sorted) - 1):
            percent = (idx + 1) / len(nodes_sorted) * 100
            print(f"   Sorting progress: {idx + 1}/{len(nodes_sorted)} ({percent:.1f}%)", end='\r')

        start = offsets[node]
        end = offsets[node + 1]
        if start < end:   # node has neighbors
            # extract slice, sort, and put back
            neighbors = nbrs[start:end].tolist()
            neighbors.sort()
            nbrs[start:end] = array('I', neighbors)

    if show_progress:
        print()   # newline after progress

    # ------------------------------------------------------------------
    # Write the binary output file.
    # ------------------------------------------------------------------
    print("Writing binary output...")
    with open(output_bin_path, 'wb') as outf:
        for idx, node in enumerate(nodes_sorted):
            if show_progress and (idx % 10000 == 0 or idx == len(nodes_sorted) - 1):
                percent = (idx + 1) / len(nodes_sorted) * 100
                print(f"   Writing progress: {idx + 1}/{len(nodes_sorted)} ({percent:.1f}%)", end='\r')

            outf.write(struct.pack('I', node))
            outf.write(struct.pack('I', deg[node]))
            start = offsets[node]
            end = offsets[node + 1]
            # write all neighbors
            for nb in nbrs[start:end]:
                outf.write(struct.pack('I', nb))

    if show_progress:
        print()

    print(f"Done. Binary file written to: {output_bin_path}")

if __name__ == '__main__':
    orkut_to_bin(IN_FILENAME, OUT_FILENAME, show_progress=True)