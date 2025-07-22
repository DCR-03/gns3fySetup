#!/usr/bin/env python3
"""
create_topology.py

Recreate the “internet” topology in GNS3:
  pip install gns3fy
  python3 create_topology.py
"""

from gns3fy import Gns3Connector, Project, Node, Link
from urllib.parse import urlparse
import math

# ── Workaround: strip Pydantic internals before create ─────────────────────────
_orig_node_create = Node.create

def _patched_node_create(self, *args, **kwargs):
    self.__dict__.pop("__pydantic_initialised__", None)
    return _orig_node_create(self, *args, **kwargs)

Node.create = _patched_node_create

_orig_link_create = Link.create

def _patched_link_create(self, *args, **kwargs):
    self.__dict__.pop("__pydantic_initialised__", None)
    return _orig_link_create(self, *args, **kwargs)

Link.create = _patched_link_create
# ── End workaround ─────────────────────────────────────────────────────────────

# ── Configuration ──────────────────────────────────────────────────────────────
GNS3_SERVER = "http://10.20.10.96:80"
PROJECT_NAME = "InternetTopology"

# Ensure these names exactly match your GNS3 templates
TEMPLATES = {
    "nat":    "NAT",
    "switch": "Ethernet‑sw12",
    "router": "OpenWrt 23.05.0",
    "host":   "Alpine Linux",
}

# Four central hosts (1.1.0.1–1.1.0.4)
CENTRAL_HOSTS = [
    ("H0_1", "1.1.0.1", 5074),
    ("H0_2", "1.1.0.2", 5076),
    ("H0_3", "1.1.0.3", 5080),
    ("H0_4", "1.1.0.4", 5078),
]

# Seven branch subnets 1.1.1.0/24 – 1.1.7.0/24
BRANCHES = [
    (1, 5098, 5102, 5106, 5108),
    (2, 5100, 5112, 5116, 5118),
    (3, 5096, 5120, 5124, 5122),
    (4, 5110, 5132, 5134, 5136),
    (5, 5114, 5130, 5128, 5126),
    (6, 5104, 5082, 5084, 5086),
    (7, 5092, 5088, 5090, 5094),
]
# ── End configuration ─────────────────────────────────────────────────────────

def main():
    # Extract just the hostname for console URLs
    server_host = urlparse(GNS3_SERVER).hostname

    # Connect and create project
    connector = Gns3Connector(url=GNS3_SERVER)
    resp = connector.create_project(name=PROJECT_NAME)
    proj = Project(
        project_id=resp["project_id"],
        connector=connector
    )
    print(f"✔ Created project '{PROJECT_NAME}' (id {resp['project_id']})")

    # 1) Create NAT node
    nat = Node(
        project_id=proj.project_id,
        connector=connector,
        name="NAT1",
        template=TEMPLATES["nat"],
        x=-200, y=0
    )
    nat.create()
    print("  • NAT1 created")

    # 2) Central Ethernet switch
    central_sw = Node(
        project_id=proj.project_id,
        connector=connector,
        name="CentralSwitch",
        template=TEMPLATES["switch"],
        x=0, y=0
    )
    central_sw.create()
    print("  • CentralSwitch created")

    # 3) Four central Alpine hosts
    central_nodes = []
    for idx, (name, ip, port) in enumerate(CENTRAL_HOSTS):
        host = Node(
            project_id=proj.project_id,
            connector=connector,
            name=name,
            template=TEMPLATES["host"],
            x=0, y=150 + idx*100,
            properties={
                "adapters": 1,
                "console": f"telnet://{server_host}:{port}"
            }
        )
        host.create()
        print(f"  • {name} ({ip}) @:{port}")
        central_nodes.append(host)

    # 4) Branch routers, switches & hosts
    branch_data = []
    angle_step = 360 / len(BRANCHES)
    radius = 300

    for i, (sub, rport, h2, h3, h4) in enumerate(BRANCHES, start=1):
        angle = math.radians((i-1) * angle_step)
        rx, ry = radius * math.cos(angle), radius * math.sin(angle)

        # Router node
        r = Node(
            project_id=proj.project_id,
            connector=connector,
            name=f"R{sub}",
            template=TEMPLATES["router"],
            x=rx, y=ry,
            properties={"console": f"telnet://{server_host}:{rport}"}
        )
        r.create()

        # Branch switch
        s = Node(
            project_id=proj.project_id,
            connector=connector,
            name=f"S{sub}",
            template=TEMPLATES["switch"],
            x=rx + 100, y=ry
        )
        s.create()

        # Three branch hosts
        hosts = []
        for j, port in enumerate((h2, h3, h4), start=2):
            h = Node(
                project_id=proj.project_id,
                connector=connector,
                name=f"H{sub}_{j}",
                template=TEMPLATES["host"],
                x=rx + 200, y=ry + (j-2)*100,
                properties={
                    "adapters": 1,
                    "console": f"telnet://{server_host}:{port}"
                }
            )
            h.create()
            hosts.append(h)

        branch_data.append((r, s, hosts))
        print(f"  • Branch {sub}: R{sub}@{rport} + S{sub} + 3 hosts")

    # 5) Create links
    # NAT ↔ CentralSwitch
    Link(
        project_id=proj.project_id,
        connector=connector,
        nodes=[
            {"node_id": nat.node_id,        "adapter_number": 0, "port_number": 0},
            {"node_id": central_sw.node_id, "adapter_number": 0, "port_number": 0}
        ]
    ).create()

    # Central hosts ↔ CentralSwitch
    for idx, host in enumerate(central_nodes, start=1):
        Link(
            project_id=proj.project_id,
            connector=connector,
            nodes=[
                {"node_id": host.node_id,      "adapter_number": 0, "port_number": 0},
                {"node_id": central_sw.node_id, "adapter_number": 0, "port_number": idx}
            ]
        ).create()

    # Branch connectivity
    for idx, (r, s, hosts) in enumerate(branch_data, start=1):
        # CentralSwitch ↔ Router
        Link(
            project_id=proj.project_id,
            connector=connector,
            nodes=[
                {"node_id": r.node_id,        "adapter_number": 0, "port_number": 0},
                {"node_id": central_sw.node_id, "adapter_number": 0, "port_number": 4 + idx}
            ]
        ).create()

        # Router ↔ BranchSwitch
        Link(
            project_id=proj.project_id,
            connector=connector,
            nodes=[
                {"node_id": r.node_id, "adapter_number": 1, "port_number": 0},
                {"node_id": s.node_id, "adapter_number": 0, "port_number": 0}
            ]
        ).create()

        # BranchSwitch ↔ BranchHosts
        for port_idx, h in enumerate(hosts, start=1):
            Link(
                project_id=proj.project_id,
                connector=connector,
                nodes=[
                    {"node_id": h.node_id, "adapter_number": 0, "port_number": 0},
                    {"node_id": s.node_id, "adapter_number": 0, "port_number": port_idx}
                ]
            ).create()

    print("✔ All nodes created and linked.")

    # 6) Start all nodes
    all_nodes = [nat, central_sw] + central_nodes
    for r, s, hs in branch_data:
        all_nodes.extend([r, s] + hs)

    for node in all_nodes:
        node.start()

    print("✔ Topology is up and running!")
    print("Connect via telnet to the host consoles as per the table above.")

if __name__ == "__main__":
    main()
