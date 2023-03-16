#!/bin/python3

# Originally developed by Jiten P. of AWS Support
# adapted by ivica-k
# adapted by rick-allen-206
import boto3
import json
import argparse


COUNT_ENIS = 0
COUNT_HENIS = 0
COUNT_HENIS_LAMBDA = 0

HENI_IDS_LAMBDA = []
HENI_IDS = []
ENI_IDS = []

VERBOSE_HENI_IDS_LAMBDA = []
VERBOSE_HENI_IDS = []
VERBOSE_ENI_IDS = []

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true',
                    help='Show HENI IDs.')
parser.add_argument('-vv', '--veryverbose', action='store_true',
                    help='Show HENI IDs and their properties.')
parser.add_argument('-r', '--region', default='us-west-2',
                    help='Name of the AWS region to search in.')
parser.add_argument('-o', '--outfile',
                    help='Name or path of the output file.')
parser.add_argument('-p', '--vpc-ids', default='',
                    help='List of VPC ids separated by "," with no spaces.')
parser.add_argument('-t', '--tags', default='',
                    help='Key:Value pair of tags to filter on separted by "," with no spaces (ex Key1:Value1,Key2:Value2).')
args = parser.parse_args()
args_dict = vars(parser.parse_args())

query_filters = []
# Add vpc-id query filters to the 'query_filters' var to be pased to the boto query
if args_dict.get('vpc_ids') != '':
    query_filters.append({'Name': 'vpc-id', 'Values': args.vpc_ids.split(',')})
# Add tag query filters to the 'query_filters' var to be pased to the boto query
if args_dict.get('tags') != '':
    tag_filters = []
    for i in (args.tags).split(','):
        tmp = {}
        name = i.split(':')[0]
        value = i.split(':')[1]
        tmp['Name'] = f'tag:{name}'
        tmp['Values'] = [value]
        tag_filters.append(tmp)
    query_filters += tag_filters

ec2_client = boto3.client('ec2', region_name=args.region)
response = ec2_client.describe_network_interfaces(Filters=query_filters)

for interface in response['NetworkInterfaces']:

    ENI_IDS.append(interface.get('NetworkInterfaceId'))
    VERBOSE_ENI_IDS.append([
        interface.get('NetworkInterfaceId'),
        interface.get('OwnerId'),
        interface.get('VpcId')])

    if 'Attachment' in interface:
        eni_id = interface.get('Attachment').get('AttachmentId')
        COUNT_ENIS += 1

        if eni_id is not None:
            if 'ela-attach' in eni_id:
                COUNT_HENIS += 1
                HENI_IDS.append(interface.get('NetworkInterfaceId'))
                VERBOSE_HENI_IDS.append([
                    interface.get('NetworkInterfaceId'),
                    interface.get('OwnerId'),
                    interface.get('VpcId')])

        # check if the the attachment id has 'ela-attach' in the it and if the 'interfaceType' is Lambda.
        if eni_id is not None and interface.get('InterfaceType') is not None:
            if 'ela-attach' in eni_id and 'lambda' in interface.get('InterfaceType'):
                COUNT_HENIS_LAMBDA += 1
                HENI_IDS_LAMBDA.append(interface.get('NetworkInterfaceId'))
                VERBOSE_HENI_IDS_LAMBDA.append([
                    interface.get('NetworkInterfaceId'),
                    interface.get('OwnerId'),
                    interface.get('VpcId')])

print(f'Total number of ENIs: {COUNT_ENIS}')
print(f'Total number of hyperplane ENIs: {COUNT_HENIS}')
print(f'Total number of hyperplane ENIs used by Lambdas: {COUNT_HENIS_LAMBDA}')
print('------------------------------------------------------')

if args.verbose:
    print(f'The list of hyperplane ENIs: {HENI_IDS}')
    print(
        f'The list of hyperplane ENIs associated with Lambdas: {HENI_IDS_LAMBDA}')
    print(f'The list of ENIs: {ENI_IDS}')

if args.veryverbose:
    print(f'The verbose list of hyperplane ENIs: {VERBOSE_HENI_IDS}')
    print(
        f'The verbose list of hyperplane ENIs associated with Lambdas: {VERBOSE_HENI_IDS_LAMBDA}')
    print(f'The verbose list of ENIs: {VERBOSE_ENI_IDS}')

if args.outfile:
    with open(f'{args.outfile}', 'w') as f:
        if args.verbose:
            f.write(json.dumps(ENI_IDS, indent=2, sort_keys=True))
        elif args.veryverbose:
            f.write(json.dumps(VERBOSE_ENI_IDS, indent=2, sort_keys=True))
