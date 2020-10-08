import logging

import molot
from molot.installer import install
install(['boto3'])
import boto3

AWS_REGION = molot.envarg('AWS_REGION', description="AWS region to use")
boto3.setup_default_session(region_name=AWS_REGION)

AWS_ASSUME_ROLE_ARN = molot.envarg('AWS_ASSUME_ROLE_ARN', description="optionally provide AWS role to assume")

@molot.target(description="assumes STS role", group="aws")
def assume_role():
    """Molot target to automatically assume envconfig-specific role RoleArn.
    """

    if AWS_ASSUME_ROLE_ARN:
        logging.info("Assuming STS role")
        boto3.client('sts').assume_role(
            RoleArn=AWS_ASSUME_ROLE_ARN,
            RoleSessionName='molot-assume-role'
        )
