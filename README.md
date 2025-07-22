# gns3-setup

This repository contains a script to set up GNS3 on a Server system. It automates the installation of GNS3 and its dependencies, making it easier to get started with network simulation.

## Prerequisites

Before running the setup script, ensure you have the following:

- Access to a GNS3 server running remotely or locally.
- Desired operating systems that you would to simulate on GNS3 already installed on the server.
- Desired network devices (e.g., routers, switches) that you want to use in your GNS3 projects.
- Basic knowledge of using the command line.
- For more information on GNS3, visit the [GNS3 website](https://www.gns3.com/).

- In our first iteration in the nonCLI folder we use Alpine Linux as the base image as well as Kali Linux.
- For the switch we use a modified Ethernet switch template (we named it "Ethernet‑sw12") that comes with 12 ports.
- For the router we use OpenWrt 23.05.0 as the base image
- For the NAT we use a preconfigured NAT template that comes with GNS3.

## Usage

To set up the GNS3 topology, follow these steps:

1. Ensure you have Python 3 installed on your system.
2. Install the `gns3fy` library if you haven't already:
   ```bash
   pip install gns3fy
   ```
3. Clone this repository or download the `create_topology.py` script.
4. Modify the `GNS3_SERVER` variable in the script to point to your GNS3 server URL.
And adjust the `TEMPLATES` dictionary to match your GNS3 templates.
5. Run the script:
   ```bash
   python3 create_topology.py
   ```
6. The script will create a project named "InternetTopology" and set up the topology as described in the comments.
7. Once the script completes, you can access the GNS3 GUI to view and interact with the created topology.

## Notes

- The script automatically creates nodes, links, and starts them.
- Ensure your GNS3 server is running and accessible before executing the script.
- You can modify the script to customize the topology further, such as adding more nodes or changing configurations.
- The script uses a workaround to strip Pydantic internals before creating nodes and links, which is necessary for compatibility with the GNS3 API.
- If you encounter any issues, check the GNS3 server logs for more information.
- As I wrie this I am also working on a CLI version of this script that will allow you to create the topology from the command line without needing to modify the script directly.

