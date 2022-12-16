import json
import os, re, base64
import boto3
from msal import ConfidentialClientApplication
import requests


def lambda_handler(event, context):
    
    ssm_client = boto3.client('ssm')
    
    client_id = ssm_client.get_parameter(Name='clientId')['Parameter']['Value']
    client_secret = ssm_client.get_parameter(Name='clientSecret')['Parameter']['Value']
    scope = 'https://graph.microsoft.com/.default'
    authority='https://login.microsoftonline.com/{}'
    tenant_id = ssm_client.get_parameter(Name='tenantId')['Parameter']['Value']
    
    identifier = ssm_client.get_parameter(Name='identityUrl')['Parameter']['Value']
    redirect = ssm_client.get_parameter(Name='acsUrl')['Parameter']['Value']
    
    
    client = ConfidentialClientApplication(client_id=client_id,client_credential=client_secret,authority=authority.format(tenant_id))
    ret_dic = client.acquire_token_for_client(scope)
    token = ret_dic.get('access_token')
    
    header_dic = {
        'header_1': {
            'Authorization': 'Bearer {}'.format(token),
    	    'Content-Type': 'application/json'
        }
    }
    
    url_dic={
        'create_group': 'https://graph.microsoft.com/v1.0/groups',
        'get_template_url': "https://graph.microsoft.com/v1.0/applicationTemplates?$filter=displayName eq 'AWS IAM Identity Center (successor to AWS Single Sign-On)'",
        'create_app_url': "https://graph.microsoft.com/v1.0/applicationTemplates/{}/instantiate",
        'configure_sso_url': "https://graph.microsoft.com/v1.0/servicePrincipals/{}",
        'set_saml_url': "https://graph.microsoft.com/v1.0/applications/{}",
        'certificate_url': 'https://graph.microsoft.com/v1.0/servicePrincipals/{}/addTokenSigningCertificate',
        'add_group': 'https://graph.microsoft.com/v1.0/servicePrincipals/{}/appRoleAssignedTo'
    }
    

    
    application_ids = create_aws_app(url_dic,header_dic)
    
    
    if application_ids[2] == 201:
        configure_saml(url_dic,header_dic,application_ids,identifier,redirect)
        certificate(url_dic,header_dic,application_ids)
        group_ids = create_groups(url_dic,header_dic)
        add_groups(url_dic,header_dic,group_ids,application_ids)
        
        
        return {
            'statusCode': 200,
            "body": "success"
        } 
    
    
def add_groups(url_dic,header_dic,group_ids,ids):
    for g_id in group_ids:
        data ={
            'principalId': g_id, ##group id
            'resourceId': ids[0], ## app object id
            'appRoleId': ids[3] ## app role id
        }
        r = requests.post(url_dic['add_group'].format(ids[0]), headers=header_dic['header_1'],json=data)
        #print(r.status_code)



def create_groups(url_dic,header_dic):
    group_name = ['admin-group', 'power-user-group', 'read-only-group']
    group_ids = []
    for name in group_name:
        group_data ={
            'displayName': name,
        	'mailEnabled': False,
        	'mailNickname': name,
        	'securityEnabled': True,
        	'groupTypes': []
        }
        r = requests.post(url_dic['create_group'], headers=header_dic['header_1'],json=group_data)
        result = r.json()
        group_ids.append(result['id'])
    return group_ids


def create_aws_app(url_dic,header_dic):
    
    r = requests.get(url_dic['get_template_url'], headers=header_dic['header_1'])
    result = r.json()
    template_id = result['value'][0]['id']
    
    body ={
	    'displayName': 'AWS Single Sign-on'
    }
    r1 = requests.post(url_dic['create_app_url'].format(template_id),headers=header_dic['header_1'],json=body)
    result1 = r1.json()
    sp_id = result1['servicePrincipal']['id']
    app_id = result1['application']['id']
    role_id = result1['application']['appRoles'][0]['id']

    return[sp_id,app_id,r1.status_code,role_id]


def configure_saml(url_dic,header_dic,ids,identifier,redirect):
    body2 ={
	    'preferredSingleSignOnMode': 'saml'
    }

    check_code = 0
    while(check_code != 204):
        r2 = requests.patch(url_dic['configure_sso_url'].format(ids[0]),headers=header_dic['header_1'],json=body2)
        check_code = r2.status_code

    body3 = {
    	"web": {
        	"redirectUris": [
          		redirect
        	] 
      	},
      	"identifierUris": [
        	identifier
      	]
    }
    check_code = 0
    while(check_code != 204):
        r3 = requests.patch(url_dic['set_saml_url'].format(ids[1]),headers=header_dic['header_1'],json=body3)
        check_code = r3.status_code


def certificate(url_dic,header_dic,ids):
    body4 ={
        "displayName":"CN=AWSSingleSignOn",
        "endDateTime": None
    }
    r4 = requests.post(url_dic['certificate_url'].format(ids[0]),headers=header_dic['header_1'],json=body4)

    thumbprint = r4.json()['thumbprint']

    body5={
        "preferredTokenSigningKeyThumbprint": thumbprint
    }
    r5 = requests.patch(url_dic['configure_sso_url'].format(ids[0]),headers=header_dic['header_1'],json=body5)

