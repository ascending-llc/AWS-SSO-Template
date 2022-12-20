# AWS-SSO-Template
It's an open source project for business to setup SSO service with AWS SSO within 30 mins

Clone this repo on your local first

### Step 1:
Download ASCENDING App from your Azure AD.
- Go to your Azure AD and record your **tenant ID**
- Click Enterprise applications, Click + New application and Search for ASCENDING app
- After downloading this app, go to App registrations and select this app, record its **application (client) ID**
- Click Certificates & secrets to create a new client secret and record the **secret value**

### Step 2:
Enable SSO service in your AWS console
- Log in your AWS console, go to IAM Identity Center, enable it if not alreay, and go to settings, click Actions and choose **Change identity source** 
- Choose **External identity provider** and click next
- Record **IAM Identity Center Assertion Consumer Service (ACS) URL** and **IAM Identity Center issuer URL**

### Step 3:
Deploy cloudformation templates provided in this repo (**Prerequisite: install AWS sam cli and AWS cli** )
- Deploy **azure-parameters-step-1.yaml** in your AWS console first, and input the values recorded from **step 1** accordingly (leave **SCIMEndpoint** and **AccessToken** as default for now)
- Open your terminal, and go to the root directory of this repo
- Run the following sam commands to build and deploy **azure-sso-app-step-2.yaml**
    - sam build -t ./cft/azure-sso-app-step-2.yaml
    - sam deploy --s3-bucket {the bucket name when you deploy parameters template} --stack-name {the name for this stack} --capabilities CAPABILITY_NAMED_IAM --region {your aws region} --parameter-overrides ParameterStack={the stack name for the parameters template}
- There are two lambdas will be created in your AWS account, run the lamda function fisrt (not the provison one)
- After the first lambda function ran successfully, go to your AWS IAM identity center, and enable auto provisioning, record the SCIMEndpoint and AccessToken
- Update **azure-parameters-step-1.yaml** stack in your AWS console by providing SCIMEndpoint and AccessToken paramters values you just got
- Run the second lamda function (provison) to setup auto provisoning between you AWS and Azure AD





