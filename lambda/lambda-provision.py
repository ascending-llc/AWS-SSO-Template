import json
import os, re, base64
import boto3
from msal import ConfidentialClientApplication
import requests


def lambda_handler(event, context):
    SecretArn = os.environ.get("SecretArn")
    scope = os.environ.get("GraphScope")
    authority= os.environ.get("GraphAuthority")
    beta_url = os.environ.get("GraphBetaUrl")
    graph_url = os.environ.get("GraphUrl")

    secrets_client = boto3.client("secretsmanager")
    response = secrets_client.get_secret_value(SecretId=SecretArn)
    secrets = json.loads(response['SecretString'])

    client_id = secrets['clientId']
    client_secret = secrets['clientSecret']
    tenant_id = secrets['tenantId']
    secret_url = secrets['SCIMEndpoint']
    secret_token = secrets['AccessToken']

    client = ConfidentialClientApplication(client_id=client_id,client_credential=client_secret,authority=authority.format(tenant_id))
    ret_dic = client.acquire_token_for_client(scope)
    token = ret_dic.get('access_token')
    
    
    header_dic = {
        'header_2': {
            'Authorization': 'Bearer {}'.format(token)
        }
    }
    
    url_dic={
        'provision_template': '{}{}/synchronization/templates',
        'create_job': '{}{}/synchronization/jobs',
        'connection': '{}{}/synchronization/jobs/{}/validateCredentials',
        'save_secret': '{}{}/synchronization/secrets',
        'start_provision': '{}{}/synchronization/jobs/{}/start',
        'get_sp': "{}servicePrincipals?$filter=displayName eq 'AWS Single Sign-on'"
    }


    
    app_id = get_sp_id(url_dic,header_dic,graph_url)
    job_template_id = provision_job(url_dic,header_dic,app_id,beta_url)
    job_id = create_provision_job(url_dic,header_dic,app_id,job_template_id,beta_url)
    connection_code = make_connection(url_dic,header_dic,app_id,job_id,secret_url,secret_token,beta_url)
    if connection_code == 204:
        save_connection(url_dic,header_dic,app_id,secret_url,secret_token,beta_url)
        r = requests.post(url_dic['start_provision'].format(beta_url,app_id,job_id), headers=header_dic['header_2'])
    
        return {
            'statusCode': 200,
            "body": "success"
        }



def get_sp_id(url_dic,header_dic,graph_url):
    r = requests.get(url_dic['get_sp'].format(graph_url), headers=header_dic['header_2'])
    app_id = r.json()['value'][0]['id']
    return app_id


def provision_job(url_dic,header_dic,app_id,beta_url):
    r = requests.get(url_dic['provision_template'].format(beta_url,app_id), headers=header_dic['header_2'])
    job_template_id = r.json()['value'][0]['id']
    return job_template_id


def create_provision_job(url_dic,header_dic,app_id,job_template_id,beta_url):
    data = {
        "templateId": job_template_id
    }
    r = requests.post(url_dic['create_job'].format(beta_url,app_id), headers=header_dic['header_2'],json=data)
    job_id = r.json()['id']

    return job_id


def make_connection(url_dic,header_dic,app_id,job_id,secret_url,secret_token,beta_url):
    data ={
        "credentials": [ 
            { 
                "key": "BaseAddress", "value": secret_url
            },
            {
                "key": "SecretToken", "value": secret_token
            }
        ]
    }
    r = requests.post(url_dic['connection'].format(beta_url,app_id,job_id), headers=header_dic['header_2'],json=data)
    
    return r.status_code


def save_connection(url_dic,header_dic,app_id,secret_url,secret_token,beta_url):
    data ={
        "value": [ 
            { 
                "key": "BaseAddress", "value": secret_url
            },
            {
                "key": "SecretToken", "value": secret_token
            }
        ]
    }
    r = requests.put(url_dic['save_secret'].format(beta_url,app_id), headers=header_dic['header_2'],json=data)
    return r.status_code


