import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from pprint import pprint
import os

ec2 = None
client = None


def authenticate_credentials(access_key, secret_key, session_token):
    """Modify the global ec2 variable with the correct AWS login credentials"""
    my_config = Config(
        region_name="us-east-1",
    )
    # authorize resource
    global ec2
    ec2 = boto3.resource(
        "ec2",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        config=my_config,
    )
    # authorize client
    global client
    client = boto3.client(
        "ec2",
        config=my_config,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
    )


def create_key_pair(key_pair_name):
    """Create a new key pair with a provided name and story to a local file"""
    pem_outfile = open(f"{key_pair_name}.pem", "w")
    response = ec2.create_key_pair(KeyName=key_pair_name)
    key_pair = str(response.key_material)
    pem_outfile.write(key_pair)
    print(f"Create Key Pair: {response}")
    return response


def delete_key_pair(key_pair_name):
    """Delete a key pair with a provided name"""
    try:
        response = client.delete_key_pair(KeyName=key_pair_name)
    except ClientError as e:
        print(e)
    if os.path.exists(f"{key_pair_name}.pem"):
        os.remove(f"{key_pair_name}.pem")
    print(f"Delete Key Pair: {response}")
    return response


def create_instance(
    security_group, security_group_id, key_pair_name, max_count=1
):
    """Create a new instance and return with its ip address"""
    instances = ec2.create_instances(
        ImageId="ami-0f82752aa17ff8f5d",
        MinCount=1,
        MaxCount=max_count,
        InstanceType="t2.micro",
        KeyName=key_pair_name,
        SecurityGroupIds=[
            security_group_id,
        ],
        SecurityGroups=[
            security_group,
        ],
    )
    # wait for instance to be in running state
    instances[0].wait_until_running()
    # update the attributes of the Instance resource
    instances[0].reload()
    print(f"Create instance: {instances[0]}")
    print(f"Instance ip address {instances[0].public_ip_address}")
    print(f"Instance id {instances[0].instance_id}")
    return instances[0].public_ip_address


def start_instance(instance_id):
    """Start an instance with a provided instance id"""
    try:
        ec2.start_instances(InstanceIds=[instance_id], DryRun=True)
    except ClientError as e:
        if "DryRunOperation" not in str(e):
            raise

    # Dry run succeeded, run start_instances without dryrun
    try:
        response = ec2.start_instances(InstanceIds=[instance_id], DryRun=False)
        print(response)
    except ClientError as e:
        print(e)


def stop_instance(instance_id):
    """Stop an instance with a provided instance id"""
    try:
        ec2.stop_instances(InstanceIds=[instance_id], DryRun=True)
    except ClientError as e:
        if "DryRunOperation" not in str(e):
            raise

    # Dry run succeeded, call stop_instances without dryrun
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id], DryRun=False)
        print(response)
    except ClientError as e:
        print(e)


def create_security_group(security_group_name):
    """Create a new security group"""
    response = client.describe_vpcs()
    vpc_id = response.get("Vpcs", [{}])[0].get("VpcId", "")
    try:
        response = client.create_security_group(
            GroupName=security_group_name,
            Description=security_group_name,
            VpcId=vpc_id,
        )
        security_group_id = response["GroupId"]
        print(f"Security Group Created {security_group_id} in vpc {vpc_id}.")

        # SSH rules
        data = client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "Ipv6Ranges": [{"CidrIpv6": "::/0"}],
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 80,
                    "ToPort": 80,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                },
            ],
        )
        print(f"Ingress Successfully Set {data}")
        return security_group_id
    except ClientError as e:
        print(e)


def delete_security_group(security_group_id):
    """Delete a security group with a provided id"""
    # Delete security group
    try:
        response = ec2.delete_security_group(GroupId=security_group_id)
        print(f"Security Group Deleted: {response}")
    except ClientError as e:
        print(e)


def describe_security_group():
    """Retrieve security group information as a dictionary of {name: id}"""
    group_dict = {}
    response = client.describe_security_groups()
    # Iterate through the list of SecurityGroup objects
    for group in response["SecurityGroups"]:
        group_dict[group["GroupName"]] = group["GroupId"]
    pprint(group_dict)
    return group_dict


def describe_instances(instance_id=None):
    """Retrieve instance information"""
    response = client.describe_instances(InstanceIds=[instance_id])
    pprint(response)


def begin_creation(access_key, secret_key, session_token, key_pair_name="ec2-auto", security_group_name="ec2-security-boto"):
    """Create and AWS instance using new key pair and return the IP address"""
    # authenticate
    authenticate_credentials(access_key, secret_key, session_token)
    # check if key pair already exists, delete old one and
    # create new key pair

    delete_key_pair(key_pair_name)
    create_key_pair(key_pair_name)
    groups = describe_security_group()
    # If security group does not exist
    if not security_group_name in groups.keys():
        # create new one
        security_group_id = create_security_group(security_group_name)
    else:
        # use existing group_id
        security_group_id = groups[security_group_name]
    # create instance
    instance_ip_address = create_instance(
        security_group=security_group_name,
        security_group_id=security_group_id,
        key_pair_name=key_pair_name,
    )
    return instance_ip_address
