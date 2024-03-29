# AWS-SSO-Template
It's an open source project for business to setup SSO service with AWS SSO within 30 mins

Clone this repo on your local first

### Step 1:
Install ASCENDING SSO App from your Azure AD Gallary.<br>
- Go to your Azure AD and record your **tenant ID**<br>
<img src="screenshots/tenant.png" width="500"><br>
- Click Enterprise applications, Click + New application and Search for ASCENDING app<br>
<img src="screenshots/app_app.png" width="500"><br>
- After downloading this app, go to App registrations and select ASCENDING app, record its **application (client) ID**<br>
<img src="screenshots/app_registrations.png" width="500"><br>
- Click API permissions, and add **Application.ReadWrite.OwnerBy** and **Create groups** application type permissions shown in the screenshot. Make sure to grant admin consent so that the Status column shows green check mark.<br>
<img src="screenshots/app_permission.png" width="500"><br>
- Click Certificates & secrets to create a new client secret and record the **secret value**<br>
<img src="screenshots/app_secrets.png" width="500"><br>

### Step 2:
Enable SSO service in your AWS console
- Log in your AWS console, go to IAM Identity Center, enable it if not alreay, and go to settings, click **Actions** and choose **Change identity source**<br>
<img src="screenshots/aws_identity.png" width="500"><br>
- Choose **External identity provider** and click next<br>

- Record **IAM Identity Center Assertion Consumer Service (ACS) URL** and **IAM Identity Center issuer URL**<br>
<img src="screenshots/aws_urls.png" width="500"><br>
- Keep this page open, we need to upload a metadata file later for **IDP SAML metadata** under Identity provider metadata section<br>

### Step 3:
Deploy cloudformation templates provided in this repo<br> 
**Prerequisite: 1. Have access to your AWS console 2. install AWS sam cli and AWS cli** 
1. Deploy **azure-parameters-step-1.yaml** in your AWS by going to the CloudFormation console first, and input the parameter values recorded from **step 1** and **step 2** accordingly<br>
Leave **SCIMEndpoint** and **AccessToken** parameters as default for now. You will get these two values later and you will need to come back and update them. 

2. Open your terminal, and go to the root directory of this repo<br>
3. Run the following sam commands sequentially to build and deploy **azure-sso-app-step-2.yaml**<br>
        
        sam build -t ./cft/azure-sso-app-step-2.yaml
    <!-- tsk -->
        sam deploy --resolve-s3 --stack-name <the name for this stack> --capabilities CAPABILITY_NAMED_IAM --region <your aws region> --parameter-overrides ParameterStack=<the stack name of the azure-parameters-step-1.yaml template> customerID=<Ask Vendor to provide> SqsMeteringUsersUrl=<Ask Vendor to provide>

4. Go to your CloudFormation console, and open this azure-sso-app-step-2.yaml stack. Click Outputs, and share the Key:**FunctionRoleToShareWithVendor**'s **Value** with us<br>
5. There are three lambdas will be created in your AWS account. 
6. run the **ProvisionClientAzureEnv** lamda function fisrt<br>
    Manually run the lambda function by creating an empty event<br>
    <img src="screenshots/aws_lambda.png" width="500"><br>

- After this lambda function ran successfully:<br>
    1. There will be three sample groups created on your Azure AD account: read-only group, admin group, and power-user group<br>

    2. Go to your Azure AD and click Enterprise Applications, you will see an application called **AWS Signle Sign-on**. Click this app and navigate to **Single sign-on** on the left panel. Go to SAML Certificates section and download the **Federation Metadata XML**<br>

        <img src="screenshots/app_sso.png" width="500"><br>

    3. Upload the **Federation Metadata XML** file for **IdP SAML metadata** on the page where you opened on **STEP 2**, then you can click next to complete the setting of External identity provider<br>

        <img src="screenshots/aws_urls.png" width="500"><br>


## Setup auto provisoning between your AWS SSO and Azure AD

1. After finishing the External identity provider settings, your AWS IAM identity center will have a message to ask you enable auto provisioning, click enable and record the **SCIMEndpoint** and **AccessToken**<br>

    <img src="screenshots/aws_provisioning.png" width="500"><br>

2. Update **azure-parameters-step-1.yaml** stack in your AWS CloudFormation console by providing **SCIMEndpoint** and **AccessToken** paramter values you just got<br>


3. Manully run the second lamda function **ProvisionClientAWSEnv** to setup auto provisoning between you AWS and Azure AD<br>

4. After the second lambda function ran successfully, the three groups created by the first lambda will be automatically synced to your AWS IAM Identity Center within 40 mins, and any Azure AD users you added to these groups will be automatically synced to your AWS IAM Identity Center as well. If the auto provisioning did not work, go to the AWS Single Sign-on app on your Azure AD, and click **Provisioning** and Click **Restart provisioning** to reboot<br>

    <img src="screenshots/app_provisioning2.png" width="500"><br>



## Configure AWS SSO Account Assignment on your AWS IAM Identity Center - optional


- From previous steps, there are three groups created on your Azure AD account and synced to your AWS IAM Identity Center, record each of the Group ID and your IAM Identity Center ARN<br>

    <img src="screenshots/aws_arn.png" width="500"><br>
    <img src="screenshots/aws_id.png" width="500"><br>

- Deploy cloudformation template: **azure-sso-permission-step-3.yaml** provided in this repo on AWS CloudFormation console and input these paramters you got from previous step to create the corresponding permission sets, associated them with each of the gourps, and attached to your AWS account so that users in the groups can have the corresponding permissions to your account and sign in using SSO<br>

- Lastly, the Azure AD users has been added to your groups can login to your AWS account by going to the SSO access portal URL on your IAM Identy Center<br>
<img src="screenshots/aws_login.png" width="500"><br>





