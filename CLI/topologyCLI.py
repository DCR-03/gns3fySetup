#!/usr/bin/env python3
"""
topologyCLI.py — Dynamic CLI-based GNS3 internet topology builder

Usage example:
  python topologyCLI.py --branches 5 --hosts-per-branch 2 --central-hosts 3
"""

import argparse
from gns3fy import Gns3Connector, Project, Node, Link
from urllib.parse import urlparse
import math

# ── Pydantic workaround ──
Node.create = (lambda f: lambda self, *a, **k: (self.__dict__.pop("__pydantic_initialised__", None), f(self, *a, **k))[1])(Node.create)
Link.create = (lambda f: lambda self, *a, **k: (self.__dict__.pop("__pydantic_initialised__", None), f(self, *a, **k))[1])(Link.create)

# ── Templates ──
TEMPLATES = {
    "nat": "NAT",
    "switch": "Ethernet‑sw12",
    "router": "OpenWrt 23.05.0",
    "host": "Alpine Linux",
}

# ── Dynamic Config Generators ──
def generate_central_hosts(count, base_ip="1.1.0.", start_port=5074):
    return [(f"H0_{i+1}", f"{base_ip}{i+1}", start_port + i * 2) for i in range(count)]

def generate_branches(count, hosts_per_branch, start_port=5100):
    branches = []
    port = start_port
    for i in range(1, count + 1):
        r_port = port
        port += 1
        host_ports = [port + j for j in range(hosts_per_branch)]
        port += hosts_per_branch
        branches.append((i, r_port, *host_ports))
    return branches

# ── Topology Creator ──
def create_topology(server_url, project_name, branches, hosts_per_branch, central_hosts, start_nodes=True, dry_run=False):
    server_host = urlparse(server_url).hostname
    connector = Gns3Connector(url=server_url)

    if not dry_run:
        resp = connector.create_project(name=project_name)
        proj = Project(project_id=resp["project_id"], connector=connector)
        print(f"✔ Created project '{project_name}' (id {resp['project_id']})")
    else:
        proj = Project(name=project_name, connector=connector)
        print(f"[dry-run] Would create project '{project_name}'")

    def create_node(**kwargs):
        if dry_run:
            print(f"[dry-run] Would create node: {kwargs['name']}")
            return Node(name=kwargs["name"])
        node = Node(**kwargs)
        node.create()
        return node

    # Generate dynamic configs
    central_hosts_list = generate_central_hosts(central_hosts)
    branch_config = generate_branches(branches, hosts_per_branch)

    # NAT node
    nat = create_node(project_id=proj.project_id, connector=connector, name="NAT1", template=TEMPLATES["nat"], x=-200, y=0)

    # Central switch
    central_sw = create_node(project_id=proj.project_id, connector=connector, name="CentralSwitch", template=TEMPLATES["switch"], x=0, y=0)

    # Central hosts
    central_nodes = []
    for idx, (name, ip, port) in enumerate(central_hosts_list):
        h = create_node(
            project_id=proj.project_id, connector=connector, name=name, template=TEMPLATES["host"],
            x=0, y=150 + idx * 100,
            properties={"adapters": 1, "console": f"telnet://{server_host}:{port}"}
        )
        central_nodes.append(h)

    # Branches
    branch_data = []
    angle_step = 360 / branches
    radius = 300
    for i, (subnet, r_port, *host_ports) in enumerate(branch_config, start=1):
        angle = math.radians((i - 1) * angle_step)
        rx, ry = radius * math.cos(angle), radius * math.sin(angle)

        r = create_node(project_id=proj.project_id, connector=connector, name=f"R{subnet}", template=TEMPLATES["router"], x=rx, y=ry, properties={"console": f"telnet://{server_host}:{r_port}"})
        s = create_node(project_id=proj.project_id, connector=connector, name=f"S{subnet}", template=TEMPLATES["switch"], x=rx + 100, y=ry)

        hosts = []
        for j, port in enumerate(host_ports, start=2):
            h = create_node(
                project_id=proj.project_id, connector=connector, name=f"H{subnet}_{j}", template=TEMPLATES["host"],
                x=rx + 200, y=ry + (j - 2) * 100,
                properties={"adapters": 1, "console": f"telnet://{server_host}:{port}"}
            )
            hosts.append(h)

        branch_data.append((r, s, hosts))

    def create_link(n1, a1, p1, n2, a2, p2):
        if dry_run:
            print(f"[dry-run] Would link {n1.name} <--> {n2.name}")
            return
        Link(project_id=proj.project_id, connector=connector, nodes=[
            {"node_id": n1.node_id, "adapter_number": a1, "port_number": p1},
            {"node_id": n2.node_id, "adapter_number": a2, "port_number": p2}
        ]).create()

    # NAT ↔ Central switch
    create_link(nat, 0, 0, central_sw, 0, 0)

    # Central hosts ↔ switch
    for idx, host in enumerate(central_nodes, start=1):
        create_link(host, 0, 0, central_sw, 0, idx)

    # Branch connections
    for idx, (r, s, hs) in enumerate(branch_data, start=1):
        create_link(r, 0, 0, central_sw, 0, 10 + idx)
        create_link(r, 1, 0, s, 0, 0)
        for port_idx, h in enumerate(hs, start=1):
            create_link(h, 0, 0, s, 0, port_idx)

    print("✔ All nodes created and linked.")

    # Start nodes
    if start_nodes and not dry_run:
        all_nodes = [nat, central_sw] + central_nodes
        for r, s, hs in branch_data:
            all_nodes.extend([r, s] + hs)
        for node in all_nodes:
            node.start()
        print("✔ Topology is up and running!")

# ── CLI Parser ──
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a GNS3 internet topology.")
    parser.add_argument("--server", type=str, default="http://localhost:3080", help="GNS3 server URL")
    parser.add_argument("--project", type=str, default="InternetTopology", help="Project name")
    parser.add_argument("--branches", type=int, default=7, help="Number of branch routers (default: 7)")
    parser.add_argument("--hosts-per-branch", type=int, default=3, help="Number of hosts per branch switch (default: 3)")
    parser.add_argument("--central-hosts", type=int, default=4, help="Number of central hosts (default: 4)")
    parser.add_argument("--no-start", action="store_true", help="Do not start nodes after creation")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    args = parser.parse_args()

    create_topology(
        server_url=args.server,
        project_name=args.project,
        branches=args.branches,
        hosts_per_branch=args.hosts_per_branch,
        central_hosts=args.central_hosts,
        start_nodes=not args.no_start,
        dry_run=args.dry_run
    )
