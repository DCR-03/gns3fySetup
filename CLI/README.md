# gns3-setup CLI version
# This script allows you to create a GNS3 topology from the command line without needing to modify the script directly.
# It uses argparse to handle command line arguments for dynamic configuration of the topology.
# You can specify the number of branches, hosts per branch, and central hosts directly from the command line.
# The script will create the topology and optionally start the nodes based on the provided arguments.
# Use the --dry-run option to see what actions would be taken without actually executing them.
# This makes it easier to test configurations before applying them.