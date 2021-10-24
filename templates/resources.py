#!/usr/bin/python3

"""
This script generates CloudFormation template for VPC with 3 following
multi-az subnets:

- `Public` (Outbound internet access)
- `Private` (No internet access)
- `Protected` (Outbound internet access via NAT)
"""

import os

from troposphere import (
    Cidr,
    Equals,
    Export,
    GetAtt,
    GetAZs,
    Output,
    Parameter,
    Ref,
    Select,
    Tags,
    Template,
    ec2,
)
from troposphere.ec2 import (
    InternetGateway,
    NetworkAcl,
    NetworkAclEntry,
    PortRange,
    Route,
    RouteTable,
    Subnet,
    SubnetNetworkAclAssociation,
    SubnetRouteTableAssociation,
    VPCGatewayAttachment,
)

template = Template()
template.set_description("Template for resources")
template.set_version("2021-10-23")

parameter_env = template.add_parameter(
    Parameter(
        "Environment",
        Type="String",
        Default="dev",
        Description="Name of the environment",
    )
)

parameter_vpc_cidr_block = template.add_parameter(
    Parameter(
        "VPCCidrBlock",
        Type="String",
        Default="10.0.0.0/16",
        Description="VPC CIDR Block (eg 10.0.0.0/16)",
        AllowedPattern="((\\d{1,3})\\.){3}\\d{1,3}/\\d{1,2}",
    )
)

parameter_vpc_dns_hostnames_enabled = template.add_parameter(
    Parameter(
        "VPCDNSHostnamesEnabled",
        Type="String",
        Default="False",
        Description="Enable DNS Hostnames",
        AllowedValues=["True", "False"],
    )
)

conditional_vpc_dns_hostnames_enabled = template.add_condition(
    "VPCDNSHostnamesEnabled", Equals(Ref(parameter_vpc_dns_hostnames_enabled), "True")
)

# default tags will be added to each resource
default_tags = {"Env": Ref(parameter_env), "Owner": "app-team"}

vpc = template.add_resource(
    ec2.VPC(
        "VPC",
        CidrBlock=Ref(parameter_vpc_cidr_block),
        EnableDnsHostnames=Ref(conditional_vpc_dns_hostnames_enabled),
        EnableDnsSupport=True,
        InstanceTenancy="default",
        Tags=Tags(default_tags),
    )
)

# index is used for selecting subset's CidrBlock, AvailabilityZone
index = 1

# Create a subnet for the private subnet
subnet_private = template.add_resource(
    Subnet(
        "Private",
        VpcId=Ref(vpc),
        CidrBlock=Select(index + 4, Cidr(GetAtt(vpc, "CidrBlock"), 16, 8)),
        AvailabilityZone=Select(index, GetAZs(Ref("AWS::Region"))),
        Tags=Tags(default_tags),
    )
)
index += 1

# Create a subnet for the public subnet
subnet_public = template.add_resource(
    Subnet(
        "Public",
        VpcId=Ref(vpc),
        CidrBlock=Select(index + 4, Cidr(GetAtt(vpc, "CidrBlock"), 16, 8)),
        AvailabilityZone=Select(index, GetAZs(Ref("AWS::Region"))),
        Tags=Tags(default_tags),
    )
)

index += 1

# Create a subnet for the protected subnet
subnet_protected = template.add_resource(
    Subnet(
        "Protected",
        VpcId=Ref(vpc),
        CidrBlock=Select(index + 4, Cidr(GetAtt(vpc, "CidrBlock"), 16, 8)),
        AvailabilityZone=Select(index, GetAZs(Ref("AWS::Region"))),
        Tags=Tags(default_tags),
    )
)

# Create GateWay, which will allow Internet Access through your Route Table.
# This will make it possible for the accounts to flow traffic in between
# the subnets
internet_gateway = template.add_resource(
    InternetGateway("InternetGateway", Tags=Tags(default_tags))
)

# Attach out GW to our VPC
gateway_attachment = template.add_resource(
    VPCGatewayAttachment(
        "AttachGateway", VpcId=Ref(vpc), InternetGatewayId=Ref(internet_gateway)
    )
)

# Create Route table and route entry for API Gateway
route_table = template.add_resource(
    RouteTable("RouteTable", VpcId=Ref(vpc), Tags=Tags(default_tags))
)

route = template.add_resource(
    Route(
        "Route",
        DependsOn="AttachGateway",
        GatewayId=Ref(internet_gateway),
        DestinationCidrBlock="0.0.0.0/0",
        RouteTableId=Ref(route_table),
    )
)

# Attach all our subnets to our new Route Tables
private_sub_route_table = template.add_resource(
    SubnetRouteTableAssociation(
        "SubnetPrivateRouteAssociation",
        SubnetId=Ref(subnet_private),
        RouteTableId=Ref(route_table),
    )
)
public_sub_route_table = template.add_resource(
    SubnetRouteTableAssociation(
        "SubnetPublicRouteAssociation",
        SubnetId=Ref(subnet_public),
        RouteTableId=Ref(route_table),
    )
)
protected_sub_route_table = template.add_resource(
    SubnetRouteTableAssociation(
        "SubnetProtectedRouteAssociation",
        SubnetId=Ref(subnet_protected),
        RouteTableId=Ref(route_table),
    )
)

# A ACL will allow and deny traffic at a network level to a Subnet.
# This is what we need to modify our private subnet.
# We still want traffic to flow between our account.
# Deny the traffic on port 80 (internet access)

# Create one ACL for the VPC
network_acl = template.add_resource(
    NetworkAcl("NetworkAcl", VpcId=Ref(vpc), Tags=Tags(default_tags))
)

# Create an ACL for each subnet, this will make it possible for the
# subnets to flow traffic between
subnet_private_network_acl_association = template.add_resource(
    SubnetNetworkAclAssociation(
        "SubnetPrivateNetworkAclAssociation",
        SubnetId=Ref(subnet_private),
        NetworkAclId=Ref(network_acl),
    )
)

subnet_public_network_acl_association = template.add_resource(
    SubnetNetworkAclAssociation(
        "SubnetPublicNetworkAclAssociation",
        SubnetId=Ref(subnet_public),
        NetworkAclId=Ref(network_acl),
    )
)

subnet_protected_network_acl_association = template.add_resource(
    SubnetNetworkAclAssociation(
        "SubnetProtectedNetworkAclAssociation",
        SubnetId=Ref(subnet_protected),
        NetworkAclId=Ref(network_acl),
    )
)

# This will open the port 80 and allow internet access to the public subnet
outbound_http_acl_public = template.add_resource(
    NetworkAclEntry(
        "OutBoundHTTPNetworkAclEntryPrivate",
        NetworkAclId=Ref(subnet_public_network_acl_association),
        RuleNumber="100",
        Protocol="6",
        PortRange=PortRange(To="80", From="80"),
        Egress="true",
        RuleAction="allow",
        CidrBlock="0.0.0.0/0",
    )
)

# This will deny the port 80 to the private subnet
outbound_http_acl_private = template.add_resource(
    NetworkAclEntry(
        "OutBoundHTTPNetworkAclEntryPublic",
        NetworkAclId=Ref(subnet_private_network_acl_association),
        RuleNumber="100",
        Protocol="6",
        PortRange=PortRange(To="80", From="80"),
        Egress="true",
        RuleAction="deny",
        CidrBlock="0.0.0.0/0",
    )
)

# Adding Elastic IP, to connect with NAT, to allow access to internet with
# outbound traffic
nat_eip = template.add_resource(
    ec2.EIP("NatEip", Domain="vpc", Tags=Tags(default_tags))
)

# Adding the subnet to the NatGateway
nat = template.add_resource(
    ec2.NatGateway(
        "Nat",
        AllocationId=GetAtt(nat_eip, "AllocationId"),
        SubnetId=Ref(subnet_protected),
        Tags=Tags(default_tags),
    )
)

# Adding the Nat to the subnet route table
template.add_resource(
    ec2.Route(
        "NatRoute",
        RouteTableId=Ref(protected_sub_route_table),
        DestinationCidrBlock="0.0.0.0/0",
        NatGatewayId=Ref(nat),
    )
)

template.add_output(
    [
        Output(
            "VPC", Description="Create VPC", Value=Ref(vpc), Export=Export(name="VPC")
        ),
        Output(
            "PrivateSubnet",
            Description="Create private subnet",
            Value=Ref(subnet_private),
            Export=Export(name="private"),
        ),
        Output(
            "PublicSubnet",
            Description="Create public subnet",
            Value=Ref(subnet_public),
            Export=Export(name="public"),
        ),
        Output(
            "ProtectedSubnet",
            Description="Create protected subnet",
            Value=Ref(subnet_protected),
            Export=Export(name="protected"),
        ),
    ]
)

output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "output")

# created dir if not exist
os.makedirs(output_folder, exist_ok=True)

with open(
    os.path.join(output_folder, "resources.yaml"),
    mode="w",
) as w:
    w.write(template.to_yaml())
