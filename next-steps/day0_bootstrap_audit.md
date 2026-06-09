# Day-0 Terraform Rebuild & Bootstrap Audit Report

This document contains a comprehensive review of the infrastructure-as-code (Terraform) and application deployment configurations for the Patient Management System. It evaluates whether a new engineer can successfully provision the entire platform from scratch (Day-0 deployment) and perform a rebuild (`terraform destroy && terraform apply`) without undocumented manual intervention.

---

## 1. Rebuild Safety Audit (Destroy / Apply Loop)

We evaluated the behavior of every resource during a complete teardown and rebuild cycle.

| Resource / Module | Rebuild Safety | Reason & Blockers |
|---|---|---|
| **VPC & Endpoints** (`module.vpc`) | **YES** | Custom VPC subnets, route tables, security groups, and interface endpoints (SSM, Secrets Manager, EC2 Messages) destroy and recreate cleanly. |
| **KMS CMK** (`module.kms`) | **CONDITIONAL** | AWS KMS keys have a deletion window of 7 to 30 days. Running `terraform destroy` schedules the key for deletion; it is not deleted instantly. However, Terraform is able to create a new key and update aliases during the subsequent `apply`. Any data encrypted with the old key becomes permanently unrecoverable. |
| **Secrets Manager** (`module.secrets`) | **NO** | **Blocker:** AWS Secrets Manager does not delete secrets instantly; they are scheduled for deletion with a minimum recovery window of 7 days. Running `terraform destroy` followed immediately by `terraform apply` will fail with an `InvalidRequestException` because a secret with the name `patient-app-secret` already exists in a deleted state. |
| **RDS Database** (`module.rds`) | **YES** | Automatically recreated because deletion protection is disabled (`rds_deletion_protection = false`) and final snapshot is skipped (`rds_skip_final_snapshot = true`). Recreating the DB wipes all data. |
| **S3 Document Bucket** (`module.s3`) | **NO** | **Blocker:** S3 buckets cannot be deleted if they contain objects. Since `force_destroy = true` is **not** set in [s3/main.tf](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/terraform/modules/s3/main.tf), `terraform destroy` will fail if any patient documents have been uploaded. |
| **IAM Roles & Policies** (`module.iam`) | **YES** | Recreates cleanly. Policies dynamically inherit S3/KMS/Secret ARNs from Terraform variables. |
| **Launch Template & ASG** (`module.launch-template`/`asg`) | **YES** | The Launch Template and Auto Scaling Group recreate cleanly. The ASG uses `create_before_destroy = true` to handle transitions safely. |
| **Load Balancer (ALB)** (`module.asg`) | **YES** | ALB, target groups, and listeners are recreated cleanly. |
| **Route53 DNS Records** (`module.dns`) | **YES** | Record aliases point directly to the newly created ALB and CloudFront distributions. |
| **Frontend S3 Bucket** (`module.frontend`) | **NO** | **Blocker:** Similar to the document S3 bucket, `force_destroy = true` is **not** set in [frontend/main.tf](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/terraform/modules/frontend/main.tf). If the frontend bundle has been uploaded, `terraform destroy` will fail. |
| **CloudFront Distribution** (`module.frontend`) | **YES** | Recreates cleanly, but takes **5 to 15 minutes** to create or disable/delete, slowing down the rebuild loop. |

---

## 2. External Dependency Analysis

The following dependencies are not provisioned by Terraform and must be prepared beforehand:

1. **Domain Name Registration**: A domain name (e.g., `lavenbloom.xyz`) must be registered externally and its nameservers pointed to AWS.
2. **Route53 Public Hosted Zone**: A Route53 public hosted zone for the domain must already exist in the AWS account. Terraform queries this zone via `data "aws_route53_zone" "primary"` to create the DNS alias records.
3. **ACM SSL/TLS Certificate**: A wildcard SSL certificate (e.g., `yourdomain.com` and `*.yourdomain.com`) must be manually requested and validated in AWS Certificate Manager in the `us-east-1` region (required for CloudFront distributions). The certificate ARN must be provided in `terraform.tfvars`.
4. **Git Repository Access**: The backend EC2 instance clones the codebase directly from GitHub. If the repository is private, the clone will fail because no SSH key, Git credentials, or Personal Access Token (PAT) are configured in the EC2 launch template user-data script.
5. **AWS Administrator Credentials**: The engineer running Terraform must have sufficient IAM permissions to create networking, IAM roles, KMS keys, databases, S3 buckets, load balancers, and CloudFront distributions.

---

## 3. Name & Secret Stability Audit

| Resource | Value Changes on Rebuild? | Runtime Impact | Terraform Handling |
|---|---|---|---|
| **S3 Buckets** | **YES** | Both the document and frontend S3 buckets use `random_string.bucket_suffix` for naming. Suffixes change on rebuild. | **Automatic for Backend / Manual for Frontend:** The backend bucket name is updated in the Secrets Manager secret automatically. However, the frontend build/deployment scripts must be updated to target the new frontend bucket name. |
| **Secrets Manager ARN** | **YES** | AWS appends a random suffix to the secret ARN upon creation. | **Automatic:** The new ARN is dynamically injected into the Launch Template user-data. |
| **Secret values** | **YES** | `db_host` (RDS endpoint) and `s3_bucket_name` change because the database endpoint and S3 bucket suffix change. | **Automatic:** Terraform automatically resolves the new RDS endpoint and S3 bucket name and updates the secret value. |
| **KMS Key ARN** | **YES** | Recreating the KMS key results in a new key ID and ARN. | **Automatic:** Terraform updates the S3 bucket policy and backend IAM policies with the new ARN. *Warning:* Any encrypted backup files from the old key are rendered permanently unreadable. |
| **RDS Endpoint** | **YES** | RDS instance DNS name changes. | **Automatic:** Terraform injects the new endpoint into Secrets Manager. |
| **ALB & CloudFront DNS** | **YES** | The default endpoints assigned by AWS (e.g., `xxx.cloudfront.net`) change. | **Automatic:** Route53 DNS records update automatically to point to the new endpoints. |

---

## 4. Data Loss Analysis

Running `terraform destroy` causes absolute data loss for the following resources:
* **RDS Database**: All patient records, user accounts, and audit logs are wiped. No final backup is taken because `rds_skip_final_snapshot = true` is set.
* **S3 Document Bucket**: All patient document uploads (PDFs, images) are permanently deleted.
* **KMS Key**: The master key is scheduled for deletion, rendering any external backups of S3 objects encrypted with this key unreadable.

*Verdict on Data Loss:* Expected and acceptable for testing/staging environments, but highly critical for production. The main issue is that data presence actively blocks the `terraform destroy` command from completing successfully due to S3 bucket deletion rules.

---

## 5. Application Bootstrap Validation

We audited the backend user-data bootstrap script ([user-data.sh.tftpl](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/terraform/modules/launch-template/templates/user-data.sh.tftpl)):

1. **Repository Cloning**: Runs `git clone ${git_repo_url}`.
   * **Blocker:** If the git repository is private, cloning will fail unless credentials or SSH keys are injected.
2. **Checkout configured tag**: Runs `git checkout ${git_tag}`. Successful if the tag exists on the remote repository.
3. **Build Virtual Environment**: Runs `python3 -m venv venv`.
   * **Safe:** The script installs `python3-venv` and `python3-pip` via `apt-get` beforehand, ensuring dependencies are available on Ubuntu 22.04.
4. **Install Python dependencies**: Installs packages from `requirements.txt`.
   * **Safe:** PyMySQL is used (a pure-python database driver), which avoids the need for local MySQL development headers on the host.
5. **Retrieve Secrets & Connect to RDS**:
   * **Safe:** The EC2 instances are in private subnets, but they access Secrets Manager via VPC interface endpoints (`aws_vpc_endpoint.secretsmanager`). NAT Gateways are also enabled to allow outbound internet traffic. The instance profile `PatientManagementAppRole` successfully authorizes Secrets Manager reads.
6. **Start FastAPI**:
   * **Safe:** The systemd service is configured properly, and database schema migration runs automatically on application startup via `Base.metadata.create_all(bind=engine)` inside [__init__.py](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/backend/app/database/__init__.py).
7. **Pass ALB Health Checks**:
   * **Safe:** Gunicorn binds to `0.0.0.0:8000`, the security group allows port `8000` ingress from the ALB, and `/health` responds with `200 OK`. The ALB can successfully route traffic to the backend instances. *Note:* Unlike the legacy architecture, Nginx is not installed on the backend hosts, but it is not required since the ALB does the reverse proxying.

---

## 6. Frontend Bootstrap Validation

There is a major architectural mismatch between the documentation and the Terraform code:

* **The Documentation** ([DEPLOYMENT.md](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/docs/deployment/DEPLOYMENT.md) and [deploy.sh](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/frontend/deploy.sh)) instructs the developer to launch a **Frontend EC2 Instance**, install Nginx, build the frontend on that instance, and configure Nginx to serve the build directory.
* **The Terraform Code** ([frontend/main.tf](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/terraform/modules/frontend/main.tf)) provisions an **S3 Bucket + CloudFront Distribution** to serve the static frontend assets.

This results in the following gaps:
1. **Frontend Code Deployment**: Terraform only provisions the empty S3 bucket and CloudFront. The React application code is **never** uploaded to S3 by Terraform.
2. **Missing Deployment Script**: There is no script to build the React application locally and sync the static assets to the randomized S3 bucket.
3. **Invalid Documentation**: A new engineer following the README or `DEPLOYMENT.md` will configure an EC2 instance with Nginx, bypassing the CloudFront + S3 architecture altogether.

---

## 7. Audit Deliverables

### Rebuild-Safe Resources
These resources can be destroyed and recreated cleanly without issues:
* **VPC Networking**: VPC, subnets, route tables, internet gateway, NAT gateway, and security groups.
* **VPC Endpoints**: SSM, secretsmanager, ec2messages, ssmmessages, and S3 gateway endpoint.
* **IAM Configuration**: IAM role, instance profile, role policy attachments, and custom IAM policies.
* **Application Load Balancer (ALB)**: Load balancer, target groups, listeners, and rules.
* **DNS Records**: Route53 A-record aliases.

### Rebuild-Risk Resources
These resources will block or fail during the rebuild loop:
* **Secrets Manager Secret** (`module.secrets`): Fails during recreate because the secret name is locked in a "pending deletion" recovery state for 7 days.
* **S3 Buckets** (`module.s3` and `module.frontend`): Destroy fails if the buckets contain any patient documents or frontend static assets because `force_destroy = true` is not configured.
* **KMS Key** (`module.kms`): Suffix changes. Causes permanent data loss for existing encrypted files.
* **CloudFront Distribution** (`module.frontend`): Takes up to 15 minutes to delete and recreate, causing long delays.

### External Prerequisites
Before running `terraform apply`, a new engineer must have:
1. An active AWS account with administrator credentials.
2. A registered domain name.
3. A Route53 public hosted zone configured in the AWS account for that domain.
4. An ACM wildcard certificate requested and validated in the `us-east-1` region for the domain.
5. The domain name and ACM certificate ARN configured in `terraform/terraform.tfvars`.
6. A public Git repository (or SSH access configured on the EC2 instances if private) for code cloning.

### Manual Recovery Steps
After a rebuild (`terraform destroy && terraform apply`), the following manual steps are required to make the platform operational:
1. **Frontend Environment Configuration**: Create `/frontend/.env` and update the `VITE_API_URL` variable to point to the new Route53 API endpoint (`https://api.yourdomain.com/api`).
2. **Build and Upload Frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   aws s3 sync dist/ s3://<new-randomized-frontend-bucket-name>/ --region us-east-1
   ```
3. **Invalidate CloudFront Cache**:
   ```bash
   aws cloudfront create-invalidation --distribution-id <cf-distribution-id> --paths "/*"
   ```

### Recommended Improvements to Achieve Day-0 Success
1. **Enable S3 Force Destroy**:
   Add `force_destroy = true` to both `aws_s3_bucket.documents` and `aws_s3_bucket.frontend` to allow clean teardowns.
2. **Prevent Secrets Manager Name Collision**:
   Add a random suffix or timestamp to the secret name, or set the name to null and let AWS generate a unique secret name to avoid collision during immediate recreation.
3. **Automate Frontend Build & Upload**:
   Create a local deployment script (e.g. `deploy-frontend.sh`) that reads the Terraform outputs (CloudFront ID, frontend bucket name) and automatically builds/uploads the React application and invalidates the cache.
4. **Update Documentation**:
   Delete or rewrite the EC2-based frontend deployment instructions in `DEPLOYMENT.md` and `frontend/deploy.sh` to match the S3 + CloudFront architecture configured in Terraform.
5. **Support Private Repositories**:
   Add an optional variable for GitHub Personal Access Tokens (PAT) or configure SSH key forwarding so private repositories can be cloned during bootstrap.

---

## 8. Final Verdict

> [!WARNING]
> **GO / NO-GO VERDICT: NO-GO**

A new engineer **cannot** clone the repository, configure `terraform.tfvars`, run `terraform apply`, and obtain a fully working deployment without undocumented manual steps.

### Primary Blockers:
1. **Empty Frontend S3 Bucket**: The frontend website returns an empty bucket error or Access Denied because there is no automated process or documentation for uploading the React build to the S3 bucket.
2. **Conflicting Documentation**: The deployment guide describes manual deployment to a Frontend EC2 instance running Nginx, which conflicts with the CloudFront + S3 architecture defined in Terraform.
3. **Secret Deletion Lock**: If the engineer attempts to destroy and rebuild the infrastructure, the `terraform apply` step will fail due to the AWS Secrets Manager 7-day deletion recovery window.
4. **S3 Bucket Deletion Block**: If any files exist in the S3 buckets, `terraform destroy` will fail because the buckets are not configured with `force_destroy = true`.
