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

    secret_url = ssm_client.get_parameter(Name='SCIMEndpoint')['Parameter']['Value']
    secret_token = ssm_client.get_parameter(Name='AccessToken')['Parameter']['Value']

    client = ConfidentialClientApplication(client_id=client_id,client_credential=client_secret,authority=authority.format(tenant_id))
    ret_dic = client.acquire_token_for_client(scope)
    token = ret_dic.get('access_token')
    
    
    header_dic = {
        'header_2': {
            'Authorization': 'Bearer {}'.format(token)
        }
    }
    
    url_dic={
        'provision_template': 'https://graph.microsoft.com/beta/servicePrincipals/{}/synchronization/templates',
        'create_job': 'https://graph.microsoft.com/beta/servicePrincipals/{}/synchronization/jobs',
        'connection': 'https://graph.microsoft.com/beta/servicePrincipals/{}/synchronization/jobs/{}/validateCredentials',
        'save_secret': 'https://graph.microsoft.com/beta/servicePrincipals/{}/synchronization/secrets',
        'start_provision': 'https://graph.microsoft.com/beta/servicePrincipals/{}/synchronization/jobs/{}/start',
        'get_sp': "https://graph.microsoft.com/v1.0/servicePrincipals?$filter=displayName eq 'AWS Single Sign-on'"
    }


    
    app_id = get_sp_id(url_dic,header_dic)
    job_template_id = provision_job(url_dic,header_dic,app_id)
    job_id = create_provision_job(url_dic,header_dic,app_id,job_template_id)
    connection_code = make_connection(url_dic,header_dic,app_id,job_id,secret_url,secret_token)
    if connection_code == 204:
        save_connection(url_dic,header_dic,app_id,secret_url,secret_token)
        r = requests.post(url_dic['start_provision'].format(app_id,job_id), headers=header_dic['header_2'])
    
        return {
            'statusCode': 200,
            "body": "success"
        }



def get_sp_id(url_dic,header_dic):
    r = requests.get(url_dic['get_sp'], headers=header_dic['header_2'])
    app_id = r.json()['value'][0]['id']
    return app_id


def provision_job(url_dic,header_dic,app_id):
    r = requests.get(url_dic['provision_template'].format(app_id), headers=header_dic['header_2'])
    job_template_id = r.json()['value'][0]['id']
    return job_template_id


def create_provision_job(url_dic,header_dic,app_id,job_template_id):
    data = {
        "templateId": job_template_id
    }
    r = requests.post(url_dic['create_job'].format(app_id), headers=header_dic['header_2'],json=data)
    job_id = r.json()['id']

    return job_id


def make_connection(url_dic,header_dic,app_id,job_id,secret_url,secret_token):
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
    r = requests.post(url_dic['connection'].format(app_id,job_id), headers=header_dic['header_2'],json=data)
    
    return r.status_code


def save_connection(url_dic,header_dic,app_id,secret_url,secret_token):
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
    r = requests.put(url_dic['save_secret'].format(app_id), headers=header_dic['header_2'],json=data)
    return r.status_code


