#!/usr/bin/env python3
import argparse
import os
import sys
from copy import deepcopy
from pacu.core.enumerate_iam.main import enumerate_iam

module_info = {
    'name': 'iam__bruteforce_permissions',
    'author': 'Rhino Security Labs',
    'category': 'ENUM',
    'one_liner': 'Enumerates permissions using brute force',
    'description': "This module will automatically run through all possible API calls of supported services in order to enumerate permissions. This uses the 'enumerate-iam' library by Andres Riancho.",
    'services': ['all'],
    'prerequisite_modules': [],
    'external_dependencies': [],
}

parser = argparse.ArgumentParser(add_help=False, description=module_info['description'])

def main(args, pacu_main):
    session = pacu_main.get_active_session()
    args = parser.parse_args(args)
    print = pacu_main.print

    aws_key = session.get_active_aws_key(pacu_main.database)

    access_key = aws_key.access_key_id
    secret_key = aws_key.secret_access_key
    session_token = aws_key.session_token if aws_key.session_token else None
    region = 'us-east-1'  # You can change this to the desired region

    # Call the enumerate_iam function from the enumerate-iam library
    results = enumerate_iam(
        access_key=access_key,
        secret_key=secret_key,
        session_token=session_token,
        region=region
    )

    # Process and print the results
    allow_permissions = []
    deny_permissions = []

    print('Enumerated IAM Permissions:')
    for service, actions in results.items():
        print(f'{service}:')
        for action, result in actions.items():
            print(f'  {action}: {result}')
            if result:  # If result is not empty or False, consider it allowed
                allow_permissions.append(f'{service}:{action}')
            else:
                deny_permissions.append(f'{service}:{action}')

    # Update the active AWS key with the new permissions
    active_aws_key = session.get_active_aws_key(pacu_main.database)
    active_aws_key.update(
        pacu_main.database,
        allow_permissions=allow_permissions,
        deny_permissions=deny_permissions
    )

    # Write all the data to the Pacu DB for storage
    iam_data = deepcopy(session.IAM)
    if 'permissions' not in iam_data:
        iam_data['permissions'] = {}

    iam_data['permissions']['allow'] = allow_permissions
    iam_data['permissions']['deny'] = deny_permissions

    session.update(pacu_main.database, IAM=iam_data)

    # Prepare the summary data
    summary_data = {
        'allow': allow_permissions,
        'deny': deny_permissions,
    }

    return summary_data

def summary(data, pacu_main):
    out = ""

    total_permissions = len(data['allow'])
    out += "Num of IAM permissions found: {} \n".format(total_permissions)
    return out
