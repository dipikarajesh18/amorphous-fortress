import re

with open("ent_cover_list.txt",'r') as f:
    lines = f.readlines()
    nodes = []
    edges = []
    for line in lines:
        value_only = re.findall(r"[0-9]\.[0-9]{2}",line)
        if value_only:
            if "Nodes" in line:
                nodes.append(float(value_only[0]))
            elif "Edges" in line:
                edges.append(float(value_only[0]))

print(f"Nodes: {sum(nodes)/len(nodes)}")
print(f"Edges: {sum(edges)/len(edges)}")