######################################################################
# This script can be used to create objects for a router, multiple
# networks and multiple endpoints on each networks
# on each compute node
# You can specify network count, endpoint count.
# If not specified, it will use defaults.
#
# usage: 
# python3 ./pai.py Apply/Delete environment networkCount endpointCount SetCount SaveYAMLInformation(Y/N)  ApplyLB(Y/N) --stop-at "(ResourceName)"
######################################################################


import subprocess
import os
import uuid
import sys
from datetime import datetime
import json
import yaml
import shutil


#Helper functions
def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout

def apply(command, name):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    print(result.stdout)  
    return result.stdout

def extract_metadata(yaml_template):
    namespace = yaml_template["metadata"]["namespace"]
    kind = yaml_template["kind"]
    idName = yaml_template["metadata"]["name"]
    return namespace, kind, idName

# Function to set executable permission for a file
def set_executable_permission(filename):
    os.chmod(filename, 0o755)

#----------------------------------------------------------------------------------------
#   ROUTER
#----------------------------------------------------------------------------------------
def create_router():
    
    print(f"\nCreating Router for vpcid {vpcid}")
    
    reqid = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    router_template = template_data["routerTemplate"].copy()
    router_template["metadata"]["annotations"]["RequestID"] = reqid
    router_template["metadata"]["namespace"] = ns
    router_template["metadata"]["name"] = rName
    router_template["spec"]["vpcid"] = vpcid

    applying(router_template)


#----------------------------------------------------------------------------------------
#   ROUTING TABLE
#----------------------------------------------------------------------------------------
def create_routing_table():
    print("\nCreating CWRouting Tables")
    reqid = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    rtr_table_template = template_data["routingTableTemplate"].copy()
    rtr_table_template["metadata"]["namespace"] = ns
    rtr_table_template["metadata"]["name"] = rtrTableName
    rtr_table_template["spec"]["vpcid"] = vpcid

    for route in rtr_table_template["spec"]["routes"]:
        route["uuid"] = f"{rPrefix}-{str(uuid.uuid4())}"

    applying(rtr_table_template)

#----------------------------------------------------------------------------------------
#   INGRESS ROUTING TABLE
#----------------------------------------------------------------------------------------

def create_ingress_routing_table():
    print("\nCreating Ingress Routing Tables")
    reqid = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    ingress_rt_template = template_data["ingressRoutingTableTemplate"].copy()
    
    ingress_rt_template["metadata"]["namespace"] = ns
    ingress_rt_template["metadata"]["name"] = ingressRTName
    ingress_rt_template["spec"]["vpcid"] = vpcid

    for route in ingress_rt_template["spec"]["routes"]:
        route["uuid"] = f"{rPrefix}-{str(uuid.uuid4())}"

    applying(ingress_rt_template)
    
#----------------------------------------------------------------------------------------
#   SECURITY GROUPS
#----------------------------------------------------------------------------------------
def create_security_groups():
    print("\nCreating Security Groups")
    for sgnum in range(1, 3):
        reqid = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        global sgName
        sgName = f"{rPrefix}-{str(uuid.uuid4())}"

        sg_template = template_data["securityGroupTemplate"].copy()
        
        sg_template["metadata"]["namespace"] = ns
        sg_template["metadata"]["name"] = sgName
        sg_template["metadata"]["annotations"]["RequestID"] = reqid
        sg_template["metadata"]["labels"]["ResourceName"] = sgName
        sg_template["metadata"]["labels"]["VPCID"] = vpcid
        sg_template["spec"]["vpcid"] = vpcid
        sg_template["spec"]["rules"][0]["uid"] = f"{rPrefix}-{str(uuid.uuid4())}"
        
        applying(sg_template)
    
#----------------------------------------------------------------------------------------
#   NACLs
#----------------------------------------------------------------------------------------  
def create_nacls():

    print("\nCreating NACLs")
    for naclnum in range(1, 3):
        reqid = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        global naclName
        naclName = f"{rPrefix}-{str(uuid.uuid4())}"

        nacl_template = template_data["networkACLTemplate"].copy()
        
        nacl_template["metadata"]["namespace"] = ns
        nacl_template["metadata"]["name"] = naclName
        nacl_template["metadata"]["annotations"]["description"] = "test network ACL"
        nacl_template["spec"]["vpcid"] = vpcid
        nacl_template["spec"]["rules"][0]["uid"] = f"{rPrefix}-{str(uuid.uuid4())}"
        nacl_template["spec"]["rules"][1]["uid"] = f"{rPrefix}-{str(uuid.uuid4())}"
        
        applying(nacl_template)
    
#----------------------------------------------------------------------------------------
#   NETWORK FILES
#----------------------------------------------------------------------------------------       
def create_networks():

    print("\nCreating Networks")
    for netnum in range(1, nwcount + 1):
        reqid = f"{netnum}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        nw = f"{mz}-{str(uuid.uuid4())}"
        subnet = f"192.62.1{netnum}.0/24"
    
        nws.append(nw)

        nw_template = template_data["networkTemplate"].copy()
        
        nw_template["metadata"]["annotations"]["RequestID"] = reqid
        nw_template["metadata"]["namespace"] = ns
        nw_template["metadata"]["name"] = nw
        nw_template["spec"]["routerName"] = rName
        nw_template["spec"]["cidr"] = subnet
        nw_template["spec"]["vpcid"] = vpcid
        nw_template["spec"]["aclName"] = naclName
        nw_template["spec"]["publicGatewayUID"] = f"{rPrefix}-{str(uuid.uuid4())}"
        nw_template["spec"]["publicGatewayIP"] = f"192.21.21.{netnum}"
        nw_template["spec"]["routingTableName"] = rtrTableName
        
        applying(nw_template)
    
#----------------------------------------------------------------------------------------
#   FOREIGN NETWORK FILES
#----------------------------------------------------------------------------------------   

def create_foreign_networks():
    print("\nCreating Foreign Networks")
    
    for netnum in range(1, nwcount + 1):
        reqid = f"{netnum}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        nw = f"{fnw_prefix}-{str(uuid.uuid4())}"
        subnet = f"192.22.1{netnum}.0/28"
        print(f"for {subnet}")

        fnw_template = template_data["foreignNetworkTemplate"].copy()

        fnw_template["metadata"]["namespace"] = ns
        fnw_template["metadata"]["name"] = nw
        fnw_template["metadata"]["annotations"]["RequestID"] = reqid
        fnw_template["spec"]["routerName"] = rName
        fnw_template["spec"]["cidr"] = subnet
        fnw_template["spec"]["vpcid"] = vpcid
        fnw_template["spec"]["aclName"] = naclName
        fnw_template["spec"]["publicGatewayUID"] = f"{rPrefix}-{str(uuid.uuid4())}"
        fnw_template["spec"]["publicGatewayIP"] = f"192.82.22.{netnum}"
        fnw_template["spec"]["routingTableName"] = rtrTableName

        applying(fnw_template)
        
    
    
#----------------------------------------------------------------------------------------
#   VIRTUAL NETWORK / VNICs
#----------------------------------------------------------------------------------------

def create_vnics():
    print("\nCreating VirtualNics (VNIC)")
    nodes = run_command("kubectl -n genctl get nodes --show-labels | grep compute | awk '{print $1}'").split()
    print(f"Number of Nodes:{len(nodes)}")
    print(f"Nodes: {nodes}")
    
    global vnic_names
    fipcount = 0
    netnum = 0
    vnic_names = []

    
    for nw in nws:
        netnum += 1
        for node in nodes:
            for epnum in range(1, epcount + 1):
                reqid = f"{netnum}-{epnum}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
                vm_uuid = str(uuid.uuid4())
                uuid_val = str(uuid.uuid4())
                vm_name = f"{mz}_{vm_uuid}"
                global vnic_name
                vnic_name = f"{mz}-{uuid_val}"
                vnic_names.append(vnic_name)

                vnic_template = template_data["virtualNicTemplate"].copy()

                vnic_template["metadata"]["annotations"]["RequestID"] = reqid
                vnic_template["metadata"]["namespace"] = ns
                node_str = node.decode('utf-8')
                vnic_template["metadata"]["name"] = vnic_name
                vnic_template["metadata"]["labels"]["OwnerNamespace"] = ns
                vnic_template["metadata"]["labels"]["ResourceGroup"] = resourceGroup
                vnic_template["metadata"]["labels"]["ResourceID"] = f"{mz}-{resourceID}"
                vnic_template["metadata"]["labels"]["VPCID"] = vpcid
                vnic_template["metadata"]["labels"]["vm_name"] = vm_name
                vnic_template["metadata"]["labels"]["InstanceID"] = vm_name
                vnic_template["metadata"]["labels"]["selflink"] = vnic_name
                vnic_template["spec"]["name"] = vnic_name
                vnic_template["spec"]["network"]["Name"] = nw
                vnic_template["spec"]["network"]["Namespace"] = ns
                vnic_template["spec"]["node"]["name"] = node
                vnic_template["spec"]["floatingIP"] = f"192.121.{netnum}{epnum}.{epnum}{fipcount}"
                vnic_template["spec"]["virtualMachine"]["Name"] = vm_name
                vnic_template["spec"]["virtualMachine"]["Namespace"] = ns
                vnic_template["spec"]["sgNames"] = [f"{sgName}"]
                

                applying(vnic_template)
                
                fipcount += 1

#----------------------------------------------------------------------------------------
#   LB (Load Balancer) Files
#----------------------------------------------------------------------------------------

def create_lb():
    if loadbalancer == "yes":

        print("\nCreating LBs (Load Balancer)")

        global lb_name
        global lb_pool_name
        global lb_listener_name
        lb_name = f"{mz}-{str(uuid.uuid4())}"
        lb_pool_name = f"{mz}-{str(uuid.uuid4())}"
        lb_listener_name = f"{mz}-{str(uuid.uuid4())}"

        lb_template = template_data["loadBalancerTemplate"].copy()

        lb_template["metadata"]["namespace"] = ns
        lb_template["metadata"]["name"] = lb_name
        lb_template["spec"]["vpcid"] = vpcid

        applying(lb_template)
    else:
        return   
        
#----------------------------------------------------------------------------------------
#   LB POOL FILES
#----------------------------------------------------------------------------------------
def create_lb_pool():
    if loadbalancer == "yes":
        print("\nCreating LBPools (Load Balancer Pool)")

        lb_pool_name = f"{mz}-{str(uuid.uuid4())}"

        lbpool_template = template_data["lbPoolTemplate"].copy()

        lbpool_template["metadata"]["namespace"] = ns
        lbpool_template["metadata"]["name"] = lb_pool_name
        lbpool_template["spec"]["vpcid"] = vpcid
        lbpool_template["spec"]["lbName"] = lb_name  # Update with the LB name as needed

        applying(lbpool_template)
    else:
        return


#----------------------------------------------------------------------------------------
#   LB POOL MEMBERS
#----------------------------------------------------------------------------------------
def create_lb_pool_members():
    if loadbalancer == "yes":

        print(f"\nCreating LBPoolMembers (Load Balancer Pool Members)")

        lbpoolmember_template = template_data["lbPoolMemberTemplate"].copy()

        for num, vnic_name in enumerate(vnic_names):

            lbpoolmember_template["metadata"]["namespace"] = ns
            lbpoolmember_template["metadata"]["name"] = f"{mz}-{str(uuid.uuid4())}"
            lbpoolmember_template["spec"]["lbPoolName"] = lb_pool_name
            lbpoolmember_template["spec"]["vnicId"] = vnic_name

            applying(lbpoolmember_template)
    else:
        return
        
#----------------------------------------------------------------------------------------
#   LB LISTENERS
#----------------------------------------------------------------------------------------
def create_lb_listeners():  
    if loadbalancer == "yes":

        print("\nCreating LBListeners (Load Balancer Listeners)")

        lb_name = f"{mz}-{str(uuid.uuid4())}"
        lb_pool_name = f"{mz}-{str(uuid.uuid4())}"
        lb_listener_name = f"{mz}-{str(uuid.uuid4())}"

        lblistener_template = template_data["lbListenerTemplate"].copy()

        lblistener_template["metadata"]["namespace"] = ns
        lblistener_template["metadata"]["name"] = lb_listener_name
        lblistener_template["spec"]["vpcid"] = vpcid
        lblistener_template["spec"]["lbName"] = lb_name
        lblistener_template["spec"]["defaultPoolID"] = lb_pool_name

        applying(lblistener_template)
    else:
        return


    
#----------------------------------------APPLY--------------------------------------------------------
if sys.argv[1].lower() in ["apply", "a"]:
    if len(sys.argv) < 2:
        print("Please specify weather you want to APPLY or DELETE the resources")
        sys.exit(1)
    if len(sys.argv) < 3:
        print("Please specify the environment as pok or ve")
        sys.exit(1)

    env = sys.argv[2]

    if env == "pok":
        region_data = run_command("cat /etc/genesis/region")
        mz = region_data.split("/")[0].split("mzone")[-1].strip()
    elif env == "ve":
        region_data = run_command("cat /etc/genesis/region")
        mz = ''.join(filter(str.isdigit, str(region_data)))
    else:
        print("Please specify the environment as pok or ve")
        sys.exit(1)
    print(f"The MZONE value is: {mz}")
    mz = mz[:4]
    if len(mz) < 4:
        mz = "0" + mz

    #Taking in the Network and Endpoint counts.
    if len(sys.argv) >= 4 and int(sys.argv[3]) > 0:
            nwcount = int(sys.argv[3])
    if len(sys.argv) >= 5 and int(sys.argv[4]) > 0:
        epcount = int(sys.argv[4])

    
    #Taking in the SET count (Number of Router sets).
 
    if len(sys.argv) >= 6 and int(sys.argv[5]) > 0:
        setCount = int(sys.argv[5])
    else:
        setCount = 1
        
    
    #Flag to save the YAML structure or not
    if len(sys.argv) >= 7:
        saveFlagArg = str(sys.argv[6]).lower()
        if saveFlagArg in ["save", "s", "yes", "y"]:
            print("Will save the resources YAML to a file for reference")
            saveFlag = True
        else:
            print("Will NOT save the resources YAML to a file")
    else:
        saveFlag = False

    #Flag to apply the LoadBalancers or not
    global loadbalancer
    if len(sys.argv) >= 8:
        lbFlag = str(sys.argv[7]).lower()
        if lbFlag in ["s", "yes", "y"]:
            loadbalancer = "yes"
        else:
            loadbalancer = "no"
    else:
        loadbalancer = "no"
        
        
        
    #LOADING TEMPLATE DATA
    if os.path.exists("/root/stresstesting/template.json"):
        with open("/root/stresstesting/template.json", "r") as json_file:
            template_data = json.load(json_file)
    elif os.path.exists("/Users/hariharen/Desktop/StressTesting/stressTesting/template.json"):
        with open("/Users/hariharen/Desktop/StressTesting/stressTesting/template.json", "r") as json_file:
            template_data = json.load(json_file)
    
    
    #  RESOURCE MAP
    resource_functions = {
        "Router": create_router,
        "Routing Table": create_routing_table,
        "Ingress Routing Table": create_ingress_routing_table,
        "Security Groups": create_security_groups,
        "Nacls": create_nacls,
        "Networks": create_networks,
        "Foreign Networks": create_foreign_networks,
        "Vnics": create_vnics,
        "Loadbalancer": create_lb,
        "Lb Pool": create_lb_pool,
        "Lb Pool Members": create_lb_pool_members,
        "Lb Listeners": create_lb_listeners
    }
# SETUP DONE 


#Applying the resources
def applyResources(stop_at_resource=None):
    
    
    #Setting the variables as global for easy access
    global ns
    global rName
    global vpcid
    global rtrTableName
    global ingressRTName
    global resourceGroup
    global resourceID
    global rPrefix
    global nws
    global naclName
    global sgName
    global fnw_prefix
    ns = "st"
    rPrefix = "r007"
    rName = f"{rPrefix}-{str(uuid.uuid4())}"
    vpcid = rName
    reqid = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    sgName = ""
    naclName = ""
    rtrTableName = f"{rPrefix}-{str(uuid.uuid4())}"
    ingressRTName = f"{rPrefix}-{str(uuid.uuid4())}"
    resourceGroup = "1e749755119e4a61a3a015eb6d44ebbb"
    resourceID = "1e749755-119e-4a61-a3a0-15eb6d44ebbb"
    fnw_prefix = "0736"
    nwcount = 1
    epcount = 1
    nws = []
    

    print(f"\nnwcount: {nwcount}, epcount: {epcount}, ns: {ns}, mz: {mz}\n")
    
    #Opening the file to track the applied resources (USED FOR DELETION)   
    applied_resources_file = open("applied_resources.txt", "a")
    applied_resources_file.write(rName + "\n")
    if saveFlag:
        applied_resources_yaml = open("applied_resources.yaml", "a")
    
    
    
    def writeYaml(saveFlag, yaml_str):
        if saveFlag:
            applied_resources_yaml.write(yaml_str)
            applied_resources_yaml.write("\n")

    global applying

    def applying(template):
        yaml_str = yaml.dump(template, default_flow_style=False)
        kubectl_apply_command = f"kubectl apply -f - <<EOF\n{yaml_str}\nEOF"
        namespace, kind, idName = extract_metadata(template)
        apply(kubectl_apply_command, kind)
        formatted_string = f"{namespace}, {kind}, {idName}"
        applied_resources_file.write(formatted_string + "\n")
        writeYaml(saveFlag, yaml_str)
        
    #Writing the NameSpace for reference
    with open("ns.txt", "w") as ns_file:
        ns_file.write(ns)
    
    
    #------------------------------------------
    # APPLYING THE RESOURCES
    # ------------------------------------------
    for resource, func in resource_functions.items():
        if stop_at_resource and resource.lower() == stop_at_resource.lower():
            func()
            print(f"Stopped at {resource}. Resources until here have been applied.")
            return
        func() 
        #Done creating the resources

    applied_resources_file.close()
    if saveFlag:
        applied_resources_yaml.close()
        
    print("-------ALL THE RESOURCES ARE APPLIED-------")




def deleteResources(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
            confirmation = True
            for line in lines:
                parts = line.strip().split(", ")
                count = 0
                if len(parts) == 3:
                    namespace, kind, name = parts
                    if kind and namespace and name: 
                        if confirmation:
                            response = input(f"Do you want to proceed with deleting the resource in namespace \"{namespace}\"? (y/n): ")
                            if response.lower() in ["y", "yes"]:
                                confirmation = False  
                            else:
                                print("Stopping Deletion")
                                sys.exit(1)
                                
                        delete_command = f'kubectl delete {kind.lower()} -n {namespace} {name} --wait=false'
                        print(f"Deleting {kind} in namespace - {namespace} with name - {name}")
                        result = run_command(delete_command)
                        if result:
                            print(result)
                            count += 1
                    else:
                        print(f"Invalid line in file: {line}")
                else:
                    print(f"{line}")
            print(f"Total resources deleted: {count}")
            del_file = input("Do you wish to delete the Applied_Resources.txt file? :  ")
            if del_file.lower() in ["yes", "y"]:
                run_command(f"rm {file_path}")
            else:
                print("File is retained!")
    else:
        print("The applied_resources.txt file does NOT exist.")
    
    
    
    
if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1].lower() in ["apply", "a"]:
        stop_at_index = sys.argv.index("--stop-at") if "--stop-at" in sys.argv else -1
        if stop_at_index != -1 and stop_at_index + 1 < len(sys.argv):
            stop_at_resource = sys.argv[stop_at_index + 1].capitalize()
            for routerIndex in range(1, setCount + 1): #For number of sets of resources
                print(f"--------Creating Router Set Number {routerIndex} / {setCount} --------")
                applyResources(stop_at_resource)
        else:
            for routerIndex in range(1, setCount + 1): #For number of sets of resources
                print(f"--------Creating Router Set Number {routerIndex} / {setCount} --------")

                applyResources()  # No --stop-at flag provided, create all resources
                
                
    elif sys.argv[1].lower() in ["delete", "d"]:
        deleteResources(f"./applied_resources.txt") 
        
        
    else:
        print("Please specify if you are trying to APPLY or DELETE the resources")   
