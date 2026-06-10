# AWS Infrastructure Setup Guide (Terraform)

This guide walks you through provisioning the complete multi-tier, highly available AWS environment for the Patient Management System. All resources are created automatically using Terraform.

**Time required**: ~15–20 minutes  
**Prerequisites**: AWS account with administrator credentials, AWS CLI installed, and Terraform (~> 1.5) installed.

---

## Prerequisites (External Assets)

Before running Terraform, you must set up the following external resources. These cannot be easily automated and must be prepared beforehand:

### 1. Registered Domain Name
You must own a registered domain name (e.g., `yourdomain.com`). If you do not have one, you can purchase it through Route53 or any external registrar.

### 2. Route53 Public Hosted Zone
Create a Route53 Public Hosted Zone for your domain in your AWS account. 
* Go to **Route53** → **Hosted Zones** → **Create hosted zone**.
* Domain name: `yourdomain.com`
* Type: **Public Hosted Zone**
* Click **Create hosted zone**.
* If the domain is registered externally, update your registrar's nameservers with the four NS records assigned by Route53.
* Terraform queries this zone at runtime using data lookups to attach DNS records automatically.

### 3. AWS Certificate Manager (ACM) Wildcard SSL Certificate
You must request a wildcard SSL certificate in the **`us-east-1` (N. Virginia)** region (required for CloudFront distributions).
* Go to **AWS Certificate Manager** (switch region to `us-east-1`) → **Request certificate**.
* Certificate type: **Request a public certificate**.
* Domain names: `yourdomain.com` and `*.yourdomain.com`.
* Validation method: **DNS validation** (recommended).
* Once requested, click **Create records in Route 53** to complete validation. Wait for status to show **Issued**.
* **Copy the Certificate ARN** — you will need to input this in `terraform.tfvars`.

---

## Step 1: Configure Environment Variables

Navigate to the `terraform/` directory. You must supply your configuration values to Terraform via a `.tfvars` file.

1. Create a `terraform.tfvars` file from scratch or by copying `terraform.tfvars.example`.
2. Populate the file with the following variables:

```hcl
project_name        = "patient-mngt"
aws_region          = "us-east-1"
domain_name         = "yourdomain.com"
acm_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxx-xxxx-xxxx"

# Database configuration
database_name       = "patient_db"
database_username   = "patient_app"
database_password   = "UseAStrongSecretPassword123!" # Save this!

# Application JWT secret
jwt_secret          = "generate-a-64-char-random-hex-string-for-security"

# Git repository configuration (backend EC2 clones this at boot)
git_repo_url        = "https://github.com/rnld101/patient-mngt-v2.git"
git_tag             = "v1.0.0"
```

---

## Step 2: Initialize & Provision

Run the following commands inside the `terraform/` directory:

### 1. Initialize Terraform
Downloads the required AWS and random providers, as well as community modules (VPC, Security Groups, RDS).
```bash
terraform init
```

### 2. Validate Configuration
Checks the code syntax and structure for validity.
```bash
terraform validate
```

### 3. Generate Execution Plan
Previews the list of resources Terraform will create in your AWS account. Review this plan carefully.
```bash
terraform plan
```

### 4. Apply Execution Plan
Deploys the infrastructure. Type `yes` when prompted.
```bash
terraform apply
```
*Note: Provisioning takes about 10–15 minutes, primarily waiting for the RDS database instance to boot and the CloudFront distribution to deploy.*

---

## Step 3: Inspect Outputs

Once `terraform apply` finishes successfully, the CLI will output several important variables:

| Output | Description |
|---|---|
| `api_endpoint` | The Route53 endpoint for the Backend API (e.g. `https://api.yourdomain.com`) |
| `frontend_endpoint` | The Route53 endpoint for the Frontend React App (e.g. `https://yourdomain.com`) |
| `frontend_bucket_name` | The S3 bucket name created to host your static files |
| `cloudfront_domain_name` | The CloudFront distribution URL (e.g. `d12345.cloudfront.net`) |
| `rds_endpoint` | The private database endpoint (RDS instance) |
| `secret_arn` | The ARN of the secret created in AWS Secrets Manager |
| `kms_key_arn` | The ARN of the Customer Managed Key used for S3 encryption |

---

## Operational Notes (Rebuild Safety)

If you need to tear down the environment (`terraform destroy`) and rebuild it immediately:

* **S3 Deletion blocker**: S3 buckets cannot be deleted by AWS if they contain files. If you uploaded patient documents or built the frontend, `terraform destroy` will fail. Ensure buckets are empty or add `force_destroy = true` to the S3 bucket resources in `modules/s3/main.tf` and `modules/frontend/main.tf` before running destroy.
* **Secrets Manager 7-Day Lock**: Running `terraform destroy` schedules the secret for deletion. Running `terraform apply` immediately after will fail with a name collision error. To bypass this, append a random suffix to the secret name or delete the secret permanently using the CLI before applying:
  ```bash
  aws secretsmanager delete-secret --secret-id patient-management-secrets --force-delete-without-recovery --region us-east-1
  ```

---

**Next step**: See `docs/deployment/DEPLOYMENT.md` to build and upload your React application to the new S3 bucket.
