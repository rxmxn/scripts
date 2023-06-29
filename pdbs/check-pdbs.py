import argparse
import json
import subprocess

parser = argparse.ArgumentParser(description="Find pods with matching PDBs")
parser.add_argument("context", help="current context")

# Parse arguments
args = parser.parse_args()

# Get pod information and parse as JSON
pod_output = subprocess.check_output(["kubectl", "get", "pods",  "--context", args.context, "--all-namespaces", "-o", "json"])
pod_info = json.loads(pod_output)

# Find matching PDBs
pdb_output = subprocess.check_output(["kubectl", "get", "pdb", "--context", args.context, "--all-namespaces", "-o", "json"])
pdb_info = json.loads(pdb_output)

pods_with_pdbs = "pods_with_pdbs-"+str(args.context)+".txt"
matching_pdbs_list = []

pods_without_pdbs = "pods_without_pdbs-"+str(args.context)+".txt"
no_matching_pdbs_list = []

pdb_with_rules = "pdb_with_rules-"+str(args.context)+".txt"
pdb_with_rules_list = []

pdb_without_rules = "pdb_without_rules-"+str(args.context)+".txt"
pdb_without_rules_list = []

pdb_rules = {}

# Iterate over each pod
for pod in pod_info["items"]:
    # Extract pod name and labels
    pod_name = pod["metadata"]["name"]
    pod_labels = pod["metadata"]["labels"]

    matching_pdbs = [pdb["metadata"]["name"] for pdb in pdb_info["items"] if set(pdb["spec"]["selector"]["matchLabels"].items()).issubset(set(pod_labels.items()))]

    if not matching_pdbs:
        no_matching_pdbs_list.append(pod_name)
    else:
        matching_pdbs_list.append(pod_name)

# Iterate over each PDB to find if it has rules and if they all have at least minAvailable or maxUnavailable
for pdb in pdb_info["items"]:
    # Extract PDB name and rules
    pdb_name = pdb["metadata"]["name"]
    min_available = pdb["spec"].get("minAvailable")
    max_unavailable = pdb["spec"].get("maxUnavailable")

    # Store rules in dictionary
    pdb_rules[pdb_name] = {"min_available": min_available, "max_unavailable": max_unavailable}

    if (min_available or max_unavailable) and (min_available == 1 or max_unavailable == 1):
        pdb_with_rules_list.append(pdb_name + " " + str(pdb_rules[pdb_name]))
    else:
        pdb_without_rules_list.append(pdb_name + " " + str(pdb_rules[pdb_name]))

# Write results to file
with open(pods_with_pdbs, "w") as f:
    f.write("\n".join(matching_pdbs_list))

with open(pods_without_pdbs, "w") as f:
    f.write("\n".join(no_matching_pdbs_list))

with open(pdb_with_rules, "w") as g:
    g.write("\n".join(pdb_with_rules_list))

with open(pdb_without_rules, "w") as g:
    g.write("\n".join(pdb_without_rules_list))

print(f"{len(no_matching_pdbs_list)} pods do NOT have a matching PDB. Names written to '{pods_without_pdbs}'")
print(f"{len(matching_pdbs_list)} pods do have a matching PDB. Names written to '{pods_with_pdbs}'")

print(f"{len(pdb_without_rules_list)} pdbs have broken rules. Names written to '{pdb_without_rules}'")
print(f"{len(pdb_with_rules_list)} pdbs have properly set rules. Names written to '{pdb_with_rules}'")
