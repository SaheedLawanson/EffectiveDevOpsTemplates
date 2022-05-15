from ipaddress import ip_network
from requests import get

from troposphere import (
 Base64, ec2, GetAtt,
 Join, Output, Parameter,
 Ref, Template,
)

ApplicationName = "helloworld"
ApplicationPort = "3000"

GithubAccount = "SaheedLawanson"
GithubAnsibleURL = f"https://github.com/{GithubAccount}/ansible"

AnsiblePullCmd = \
    f"/usr/local/bin/ansible-pull -U {GithubAnsibleURL} {ApplicationName}.yaml"

PublicCidrIp = str()
ip_network(get('https://api.ipify.org').text)
t = Template()

t.set_description("Effective DevOps in AWS: HelloWorld web application")

t.add_parameter(Parameter(
    "KeyPair",
    Description="Name of an existing EC2 KeyPair to SSH",
    Type="AWS::EC2::KeyPair::KeyName",
    ConstraintDescription="must be the name of an exisiting EC2 KeyPair"
))

t.add_resource(ec2.SecurityGroup(
    "SecurityGroup",
    GroupDescription=f"Allow SSH and TCP/{ApplicationPort} access",
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp=PublicCidrIp
        ),
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=ApplicationPort,
            ToPort=ApplicationPort,
            CidrIp="0.0.0.0/0",
        ),
    ]
))

ud = Base64(Join('\n', [
    "#!/bin/bash",
    "yum install --enablerepo=epel -y git",
    "pip install ansible",
    AnsiblePullCmd,
    f"echo '*/10 * * * * {AnsiblePullCmd}' > etc/cron.d/ansible-pull"
]))

t.add_resource(ec2.Instance(
    "instance",
    ImageId="ami-25615740",
    InstanceType="t2.micro",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("KeyPair"),
    UserData=ud
))

t.add_output(Output(
    "InstancePublicIp",
    Description="Public IP of our instance",
    Value=GetAtt("instance", "PublicIp")
))

t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("", [
        "http://", GetAtt("instance", "PublicDnsName"),
        ":", ApplicationPort
    ])
))

print(t.to_json())