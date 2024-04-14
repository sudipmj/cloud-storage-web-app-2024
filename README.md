<<<<<<< HEAD
# cloud-storage-app
A simple file storage web application over AWS
=======
# **Cloud Storage Application Setup Guide**
This guide provides brief instructions for setting up and configuring the Cloud Storage Application on AWS. The application leverages various AWS services, including Elastic Beanstalk (EB), Lambda, API Gateway, RDS MySQL, S3, and SQS. Follow the steps below for a successful setup.

### configure application vars
**Create config.py in the root of the project**
Declare all the required variables
`RDS_HOST, RDS_PORT, RDS_USER, RDS_PASSWORD, RDS_DB_NAME,
    AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_BUCKET_NAME, AWS_REGION, AWS_S3_REGION, AWS_DLQ_URL`

### Access Keys Setup
**Create Access Keys:**
Generate AWS access keys with the necessary permissions for Elastic Beanstalk, S3, EC2, and SQS.

**Permission Configuration:**
Ensure that the access keys have the required permissions. Refer to the AWS IAM console.

**Secure Storage:**
Store the Access Key and Secret Key securely for future use. Consider using AWS Key Management Service (KMS) for additional security.

### RDS MySQL Database Setup
**Create RDS Instance:**
Set up an RDS MySQL database instance through the AWS RDS console.

**Table Initialization:**
Execute the sql/init.sql script to create the necessary database and tables for the application.

### S3 Bucket Setup
**Bucket Creation:**
Create an S3 bucket to store content uploaded from the Cloud Storage Application.

### SQS Queue Setup
**Create SQS Queue:**
Establish an SQS Queue and configure it as a Dead Letter Queue to collect information on failed uploads.
### Elastic Beanstalk (EB) Setup
**EB CLI Installation:**
Ensure the Elastic Beanstalk Command Line Interface (EB CLI) is installed and configured.

**EB Environment Creation:**
Use the EB CLI to initialize the EB application and create an environment. Deploy and manage the application using EB CLI commands.

    eb init -p python-3.11 cloud-sa2024  		# inits eb application
    eb create cloud-sa2024-gf02 --debug			# creates eb env 
    eb deploy --debug							# update code & deploy
    eb logs --all								# download eb logs
    eb status									# displays eb env status
    eb open										# opens created application
    eb terminate cloud-sa2024-gf02				# terminates eb env & other services

### CloudWatch Integration:
Configure the EB environment to store logs in Amazon CloudWatch for efficient log management.

### Lambda Function Setup
**Function Creation:**
Develop a Lambda function using the lambda_function.py script.

**Layer Addition:**
Upload cloud-sa2024-lambda-layer.zip as a lambda layer to include the necessary packages required for the Lambda function.

**Test Event:**
Create a test event with a sample JSON payload to test the Lambda function.
    {
        	"email": "kdb@m.city",
        	"pass": "pep",
        	"filename": "index.html"
    }

### API Gateway Setup
**Gateway Creation:**
Establish an API Gateway using the AWS API Gateway console.

**Method Configuration:**
Add a POST method to the API Gateway, linking it to the Lambda function for invocation.

**Deployment:**
Deploy the API to make it accessible for external use.

*Note:* Adhere to security best practices, manage credentials securely, and restrict permissions based on the principle of least privilege. Regularly review and update security settings as needed. Customize the setup according to specific requirements and security policies.
>>>>>>> remotes/origin/development
