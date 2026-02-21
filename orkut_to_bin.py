import os
import struct
from array import array

IN_FILENAME = "com-orkut.ungraph.txt"
OUT_FILENAME = "orkut_data.bin"

def orkut_to_bin(input_txt_path, output_bin_path, show_progress=True):
    """
    Convert an undirected edge list (text file) to the apriori binary format
    required by the All‑Pairs C program.

    The output contains for each node (in order of non‑decreasing degree):
        - original node ID (4 bytes, unsigned int)   [record id]
        - degree (4 bytes, unsigned int)             [number of features]
        - neighbor IDs (4 bytes each, sorted increasingly)
          where neighbor IDs are new feature IDs assigned by global frequency
          (1 = least frequent original node).

    Parameters
    ----------
    input_txt_path : str
        Path to the input edge list (one undirected edge per line,
        lines starting with '#' are ignored).
    output_bin_path : str
        Path where the binary output will be written.
    show_progress : bool
        If True, print progress indicators.
    """
    # ------------------------------------------------------------------
    # Pass 1: count degree of each original node
    # ------------------------------------------------------------------
    print("Pass 1: Counting degrees (global feature frequencies)...")
    deg = array('I')          # degree of each original node, index = node ID
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

            if u > max_node_id:
                max_node_id = u
            if v > max_node_id:
                max_node_id = v

            # ensure deg array is large enough
            while len(deg) <= max_node_id:
                deg.append(0)

            deg[u] += 1
            deg[v] += 1
            line_count += 1

    print(f"   Found {line_count} undirected edges. Max original node ID: {max_node_id}")

    # total number of directed neighbor entries (sum of degrees)
    total_neighbors = sum(deg)
    print(f"   Total directed neighbor entries: {total_neighbors}")

    # ------------------------------------------------------------------
    # Build mapping: original node ID -> new feature ID (1 = least frequent)
    # ------------------------------------------------------------------
    print("Building feature ID mapping (least frequent -> ID 1)...")
    # collect (degree, original_id) for all nodes that appear
    nodes_with_degree = [(deg[node], node) for node in range(1, max_node_id + 1) if deg[node] > 0]
    # sort by degree ascending, then by original ID for determinism
    nodes_with_degree.sort(key=lambda x: (x[0], x[1]))

    # map_old_to_new[original_id] = new_feature_id
    map_old_to_new = array('I', [0]) * (max_node_id + 1)
    for new_id, (_, old_id) in enumerate(nodes_with_degree, start=1):
        map_old_to_new[old_id] = new_id

    num_distinct = len(nodes_with_degree)
    print(f"   Assigned new IDs to {num_distinct} distinct features.")
    print(f"   New feature ID range: 1 .. {num_distinct}")

    # ------------------------------------------------------------------
    # Pass 2: build CSR adjacency (original IDs)
    # ------------------------------------------------------------------
    print("Pass 2: Building CSR structure (original IDs)...")
    # offsets[node] = start index of node's neighbors in nbrs array
    # offsets[node+1] = end index (exclusive)
    offsets = array('Q', [0]) * (max_node_id + 2)   # unsigned long long

    for node in range(1, max_node_id + 1):
        offsets[node + 1] = offsets[node] + deg[node]

    # nbrs holds all neighbor entries (original IDs), placed contiguously
    nbrs = array('I', [0]) * total_neighbors

    # pos is a working copy of offsets for filling
    pos = array('Q', offsets)

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

    # we no longer need 'pos'
    del pos

    # ------------------------------------------------------------------
    # Replace original neighbor IDs with new feature IDs
    # ------------------------------------------------------------------
    print("Mapping neighbor IDs to new feature IDs...")
    # Quick sanity check: the maximum original ID in nbrs should be ≤ max_node_id
    max_orig_in_nbrs = max(nbrs) if total_neighbors > 0 else 0
    print(f"   Maximum original ID in neighbor list: {max_orig_in_nbrs}")
    for i in range(total_neighbors):
        old = nbrs[i]
        new = map_old_to_new[old]
        if new == 0:
            # This should never happen if the graph is consistent
            raise ValueError(f"Original node {old} has no mapping (degree zero?)")
        nbrs[i] = new

    # Sanity check: maximum new ID should equal num_distinct
    max_new_in_nbrs = max(nbrs) if total_neighbors > 0 else 0
    print(f"   Maximum new feature ID in neighbor list: {max_new_in_nbrs} (expected {num_distinct})")

    # ------------------------------------------------------------------
    # Sort each node's neighbor list by new feature ID
    # ------------------------------------------------------------------
    print("Sorting neighbor lists (by new feature ID)...")
    # Nodes that have at least one neighbor (their degree > 0)
    active_nodes = [node for node in range(1, max_node_id + 1) if deg[node] > 0]
    # Sort by degree (vector size) ascending – this will be the output order
    active_nodes.sort(key=lambda n: deg[n])

    for idx, node in enumerate(active_nodes):
        if show_progress and (idx % 10000 == 0 or idx == len(active_nodes) - 1):
            percent = (idx + 1) / len(active_nodes) * 100
            print(f"   Sorting progress: {idx + 1}/{len(active_nodes)} ({percent:.1f}%)", end='\r')

        start = offsets[node]
        end = offsets[node + 1]
        if start < end:
            # extract slice, sort, and put back
            neighbors = nbrs[start:end].tolist()
            neighbors.sort()
            nbrs[start:end] = array('I', neighbors)

    if show_progress:
        print()

    # ------------------------------------------------------------------
    # Write binary output in the required order
    # ------------------------------------------------------------------
    print("Writing binary output...")
    with open(output_bin_path, 'wb') as outf:
        for idx, node in enumerate(active_nodes):
            if show_progress and (idx % 10000 == 0 or idx == len(active_nodes) - 1):
                percent = (idx + 1) / len(active_nodes) * 100
                print(f"   Writing progress: {idx + 1}/{len(active_nodes)} ({percent:.1f}%)", end='\r')

            # record ID = original node ID (kept for traceability)
            outf.write(struct.pack('I', node))
            # number of features = degree
            outf.write(struct.pack('I', deg[node]))
            # feature IDs (already sorted by new ID)
            start = offsets[node]
            end = offsets[node + 1]
            for nb in nbrs[start:end]:
                outf.write(struct.pack('I', nb))

    if show_progress:
        print()

    print(f"Done. Binary file written to: {output_bin_path}")
    print(f"Maximum feature ID in output: {num_distinct}")
    if num_distinct > 600000:
        print("WARNING: The number of distinct features exceeds the C program's max_feature_id (600000).")
        print("You must increase max_feature_id in main.cc to at least", num_distinct, "and recompile.")


if __name__ == '__main__':
    orkut_to_bin(IN_FILENAME, OUT_FILENAME, show_progress=True)