import json
import os, re, base64
import boto3
from msal import ConfidentialClientApplication
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def lambda_handler(event, context):
    SecretArn = os.environ.get("SecretArn")
    GraphUrl = os.environ.get("GraphUrl")
    appName = os.environ.get("AWSAppName")
    scope = os.environ.get("GraphScope")
    authority= os.environ.get("GraphAuthority")
    group_names = [name for name in os.environ.get("GroupNames").split(",") if name]

    secrets_client = boto3.client("secretsmanager")
    response = secrets_client.get_secret_value(SecretId=SecretArn)
    secrets = json.loads(response['SecretString'])

    client_id = secrets['clientId']
    client_secret = secrets['clientSecret']
    tenant_id = secrets['tenantId']
    identifier = secrets['identityUrl']
    redirect = secrets['acsUrl']
    
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
        'create_group': '{}groups',
        'get_template_url': "{}applicationTemplates?$filter=displayName eq '{}'",
        'create_app_url': "{}applicationTemplates/{}/instantiate",
        'configure_sso_url': "{}servicePrincipals/{}",
        'set_saml_url': "{}applications/{}",
        'certificate_url': '{}servicePrincipals/{}/addTokenSigningCertificate',
        'add_group': '{}servicePrincipals/{}/appRoleAssignedTo'
    }
    

    
    application_ids = create_aws_app(url_dic,header_dic,GraphUrl,appName)
    
    
    if application_ids[2] == 201:
        configure_saml(url_dic,header_dic,application_ids,identifier,redirect,GraphUrl)
        certificate(url_dic,header_dic,application_ids,GraphUrl)
        group_ids = create_groups(url_dic,header_dic,GraphUrl,group_names)
        add_groups(url_dic,header_dic,group_ids,application_ids,GraphUrl)
        
        
        return {
            'statusCode': 200,
            "body": "success"
        } 
    
def add_groups(url_dic,header_dic,group_ids,ids,graph_url):
    for g_id in group_ids:
        data ={
            'principalId': g_id, ##group id
            'resourceId': ids[0], ## app object id
            'appRoleId': ids[3] ## app role id
        }
        r = requests.post(url_dic['add_group'].format(graph_url,ids[0]), headers=header_dic['header_1'],json=data)
        #print(r.status_code)



def create_groups(url_dic,header_dic,graph_url,group_names):
    group_name = group_names
    group_ids = []
    for name in group_name:
        group_data ={
            'displayName': name,
        	'mailEnabled': False,
        	'mailNickname': name,
        	'securityEnabled': True,
        	'groupTypes': []
        }
        r = requests.post(url_dic['create_group'].format(graph_url), headers=header_dic['header_1'],json=group_data)
        result = r.json()
        group_ids.append(result['id'])
    return group_ids


def create_aws_app(url_dic,header_dic,graph_url,appName):
    r = requests.get(url_dic['get_template_url'].format(graph_url,appName), headers=header_dic['header_1'])
    result = r.json()
    template_id = result['value'][0]['id']
    
    body ={
	    'displayName': 'AWS Single Sign-on'
    }
    r1 = requests.post(url_dic['create_app_url'].format(graph_url,template_id),headers=header_dic['header_1'],json=body)
    result1 = r1.json()
    sp_id = result1['servicePrincipal']['id']
    app_id = result1['application']['id']
    role_id = result1['application']['appRoles'][0]['id']

    return[sp_id,app_id,r1.status_code,role_id]


def configure_saml(url_dic,header_dic,ids,identifier,redirect,graph_url):
    body2 ={
	    'preferredSingleSignOnMode': 'saml'
    }

    requests_session = requests.Session() #
    requests_session2 = requests.Session()
    retries = Retry( 
        total=4, 
        backoff_factor=3, 
        status_forcelist=[403, 404],
        allowed_methods= ["PATCH"]
    )
    requests_session.mount("https://", HTTPAdapter(max_retries=retries)) 
    r2 = requests_session.patch(url_dic['configure_sso_url'].format(graph_url,ids[0]),headers=header_dic['header_1'],json=body2)

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
    requests_session2.mount("https://", HTTPAdapter(max_retries=retries)) 
    r3 = requests_session2.patch(url_dic['set_saml_url'].format(graph_url,ids[1]),headers=header_dic['header_1'],json=body3)


def certificate(url_dic,header_dic,ids,graph_url):
    body4 ={
        "displayName":"CN=AWSSingleSignOn",
        "endDateTime": None
    }
    r4 = requests.post(url_dic['certificate_url'].format(graph_url,ids[0]),headers=header_dic['header_1'],json=body4)

    thumbprint = r4.json()['thumbprint']

    body5={
        "preferredTokenSigningKeyThumbprint": thumbprint
    }
    r5 = requests.patch(url_dic['configure_sso_url'].format(graph_url,ids[0]),headers=header_dic['header_1'],json=body5)

