# Repository Analysis & Presentation Assets

## Consistency Audit and Verification Report

A comprehensive review of the repository's documentation and code reveals a critical architectural mismatch. The repository contains two completely different deployment models that are inconsistent with each other:

1. **The Documentation Model** (described in [ARCHITECTURE.md](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/docs/aws/ARCHITECTURE.md), [AWS_SETUP.md](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/docs/aws/AWS_SETUP.md), and [DEPLOYMENT.md](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/docs/deployment/DEPLOYMENT.md)):
   * **Frontend**: A dedicated `t3.small` EC2 instance running Nginx on port 80 to host and serve a React SPA build.
   * **Database**: A self-managed MySQL 8.0 server installed manually on a standalone `t3.small` EC2 database instance.
   * **Compute / High Availability**: A single, standalone `t3.medium` Backend EC2 instance running FastAPI + Gunicorn, directly exposed to the internet.
   * **Network Topology**: A flat networking structure assuming public IP allocation for all instances and direct internet-facing ingress.

2. **The Terraform IaC Model** (configured in the [terraform/](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/terraform/) directory):
   * **Frontend**: Serverless hosting. An S3 bucket (public access blocked) distributed globally via a CloudFront CDN distribution using Origin Access Control (OAC).
   * **Database**: A managed AWS RDS MySQL database (engine version 8.4) deployed inside isolated database subnets.
   * **Compute / High Availability**: Backend EC2 instances booted from a Launch Template, managed by an Auto Scaling Group (ASG) in private subnets, behind an Application Load Balancer (ALB) in public subnets.
   * **Network Topology**: A strict, multi-tier VPC (`10.0.0.0/16`) spanning 2 Availability Zones (`us-east-1a`/`us-east-1b`) with Public, Private, and Database Subnets, a NAT Gateway, and Private VPC Interface Endpoints (SSM, SSMMessages, EC2Messages, Secrets Manager) + an S3 Gateway Endpoint.

### Major Inconsistencies & Deployment Gaps

* **Orphaned Frontend S3 Bucket**: Terraform provisions the S3 bucket and CloudFront distribution for the frontend, but it does not upload any frontend assets to the bucket. Meanwhile, the documentation teaches manual deployment to a frontend EC2 instance, so there is no script or documentation describing how to compile the React code and sync it to the randomized S3 bucket (`aws s3 sync dist/ s3://<random-bucket-name>`). The frontend CloudFront endpoint will display an Access Denied / Empty Bucket error out of the box.
* **Gunicorn Proxy Mismatch**: In the manual deployment docs, Nginx is installed on the backend EC2 host to proxy port 80 to localhost port 8000. In the Terraform setup, there is no Nginx on the backend hosts (which are launched in private subnets with no public IPs); instead, the ALB communicates directly with Gunicorn on port 8000.
* **VPC Endpoint vs. Internet Route**: The backend launch template user-data script configures the FastAPI systemd service but relies on NAT Gateway or VPC endpoints to fetch configurations from AWS Secrets Manager. If NAT Gateways or VPC endpoints are missing or fail, the application cannot startup.
* **Secrets Manager Immediate Re-apply Lock**: Running `terraform destroy` followed by `terraform apply` fails because AWS Secrets Manager does not instantly delete secrets (they are scheduled for deletion with a 7-day minimum recovery window). Running a rebuild will throw an `InvalidRequestException` for the `patient-management-secrets` name.
* **S3 Deletion Blocker**: Neither the document storage S3 bucket nor the frontend S3 bucket have `force_destroy = true` set. If any files (patient documents or frontend builds) are uploaded, `terraform destroy` will fail.

---

## Technical Review

### 1. Application Layer Summary
* **Overview**: A secure patient and medical document management platform that enables healthcare professionals to manage patient information and securely store associated documents.
* **Target Users**: Healthcare professionals (doctors, nurses, clinic administrators) requiring secure access to patient medical histories and diagnostic files.
* **Core Business Functionality**: Patient registration and metadata tracking (age, gender, blood group, contact details), diagnostic document upload, secure document viewing via short-lived credentials, and patient/document deletion.
* **Data Flow**: User browser client initiates HTTP requests carrying JWT tokens in the `Authorization` header. The request hits the application, which queries MySQL database tables (`users`, `patients`, `patient_documents`).
* **Document Storage Flow**: Files uploaded via `POST /api/patients/{id}/documents` are received by FastAPI, validated (file type, size), and streamed directly to a private S3 bucket using `boto3`. S3 encrypts the object at rest using SSE-KMS. The generated S3 key path (`patient_documents/<uuid>.<ext>`) is logged in the MySQL `patient_documents` table.
* **Authentication Flow**: Users register and log in via `POST /api/auth/register` and `POST /api/auth/login`. Passwords are encrypted using `bcrypt` (12 rounds). Successful login issues a signed JWT token containing the `user_id` as the subject (`sub`). Endpoints enforce per-user isolation by scoping all SQL queries to the `user_id` parsed from the JWT.

### 2. AWS Architecture Analysis (Service → Purpose → Benefit)

* **Route53**:
  * *Purpose*: Manages public DNS records for the primary domain and subdomains (pointing frontend requests to CloudFront and API requests to the ALB).
  * *Benefit*: Highly available, low-latency DNS resolution that maps user-friendly domains to AWS endpoints.
* **CloudFront**:
  * *Purpose*: Distributes static frontend React assets globally from edge locations.
  * *Benefit*: Accelerates page loads, reduces origin load, and secures static assets by avoiding direct public exposure of the S3 origin.
* **S3 (Simple Storage Service)**:
  * *Purpose*: Two distinct storage locations: one for static website assets, and one private bucket for patient diagnostic files (PDFs, images).
  * *Benefit*: Serverless, virtually infinite scalability with 99.999999999% durability, and integrated KMS encryption.
* **ALB (Application Load Balancer)**:
  * *Purpose*: Proxies public HTTP/HTTPS traffic from the internet and distributes it across backend EC2 instances in private subnets.
  * *Benefit*: Handles SSL termination (via ACM certificates), isolates backend instances from direct internet entry, and performs active health checking.
* **Auto Scaling Group (ASG)**:
  * *Purpose*: Manages backend compute nodes, automatically launching or terminating EC2 instances (Min: 1, Max: 2) based on health and traffic.
  * *Benefit*: Guarantees high availability, fault tolerance, and automated healing of compute infrastructure.
* **Launch Templates**:
  * *Purpose*: Declares the configuration template (AMI, VM size, security groups, IAM instance profile, user-data bootstrap script) for ASG-spawned EC2 instances.
  * *Benefit*: Ensures consistent, repeatable node deployments and automates software bootstrapping (cloning code, installing virtualenv, and starting services).
* **EC2 (Elastic Compute Cloud)**:
  * *Purpose*: Hosts the Python FastAPI application served by Gunicorn workers.
  * *Benefit*: Flexible virtual machines that can run specialized application runtimes inside private network boundaries.
* **RDS (Relational Database Service)**:
  * *Purpose*: Deploys a managed, private MySQL database instance in dedicated database subnets.
  * *Benefit*: Removes administrative overhead of backups, software patching, and scaling while securing sensitive patient data from public networks.
* **KMS (Key Management Service)**:
  * *Purpose*: Houses the Customer Managed Key (CMK) alias `patient-app-s3-key` that encrypts objects stored in the S3 document bucket.
  * *Benefit*: Provides centralized, auditable control over cryptographic keys with strict IAM access policies.
* **Secrets Manager**:
  * *Purpose*: Secures database credentials, JWT secret keys, and configuration parameters.
  * *Benefit*: Prevents hardcoded credentials in the repository; secrets are requested at startup and held strictly in-memory.
* **IAM (Identity and Access Management)**:
  * *Purpose*: Generates the `PatientManagementAppRole` role and instance profile containing least-privilege policies.
  * *Benefit*: Permits backend EC2 instances to retrieve credentials from Secrets Manager and read/write to S3 and KMS without using static AWS access keys.
* **VPC (Virtual Private Cloud)**:
  * *Purpose*: Logically isolates the network, establishing public, private, and database subnets across two AZs.
  * *Benefit*: Implements network security boundaries, ensuring frontend, backend, and database tiers remain isolated from one another.
* **Security Groups**:
  * *Purpose*: Acts as virtual firewalls regulating inbound and outbound traffic at the resource layer.
  * *Benefit*: Restricts network traffic to least privilege (e.g. database only permits 3306 from backend instances; backend only permits 8000 from the ALB).
* **VPC Endpoints (Interface & Gateway)**:
  * *Purpose*: Configures private endpoints inside the VPC for SSM, SSMMessages, EC2Messages, Secrets Manager, and S3.
  * *Benefit*: Allows EC2 instances in private subnets to communicate with AWS APIs without traveling over the public internet or requiring NAT transit, mitigating data exfiltration risks.

### 3. Terraform Analysis (Key Concepts and Patterns Used)
* **Modular Architecture**: Split into 10 encapsulated directories under `modules/` (such as `vpc`, `asg`, `rds`, `s3`, `iam`, `kms`), separating concerns and allowing component isolation.
* **Environment Parameterization**: Uses variables (`variables.tf` and `terraform.tfvars`) to decouple configuration from resource definitions (defining domain names, instance sizes, and regions).
* **Data Sources**: Employs lookup blocks (`data "aws_ami" "ubuntu"` and `data "aws_route53_zone" "primary"`) to dynamically query existing AWS configurations at runtime.
* **Dependency Management**: Implicitly chains modules by passing outputs from one module as inputs to another (e.g., passing `module.rds.endpoint` and `module.s3.bucket_name` directly to `module.secrets`).
* **Resource Composition**: Leverages custom resources combined with community modules (such as using `terraform-aws-modules/vpc/aws` inside `main.tf` alongside custom S3, KMS, and IAM structures).
* **State-Driven Provisioning**: Leverages state tracking (`terraform.tfstate`) to manage resource drift and clean teardown execution.
* **Dynamic Resource References**: Uses outputs (`outputs.tf`) to expose endpoints dynamically generated during provisioning (like ALB DNS name, RDS endpoints, and S3 bucket names).

### 4. Security Analysis (Control → Threat Mitigated → Benefit)

* **Private Subnets**:
  * *Threat Mitigated*: Direct brute-force attacks, port scanning, and remote code execution exploits launched from the public internet.
  * *Benefit*: Blocks all inbound traffic from the internet to backend compute nodes and the RDS database.
* **Security Groups (Micro-segmentation)**:
  * *Threat Mitigated*: Lateral movement (if one tier is compromised, the attacker accesses other tiers) and unauthorized network access.
  * *Benefit*: Isolates traffic paths so that only the ALB can reach the backend, and only the backend can reach the RDS database.
* **IAM Least Privilege**:
  * *Threat Mitigated*: Account compromise and unauthorized AWS resource manipulation if an EC2 instance is breached.
  * *Benefit*: Restricts the EC2 instance profile to a single S3 bucket, a single Secrets Manager secret, and a single KMS key.
* **Secrets Manager**:
  * *Threat Mitigated*: Credential theft through repository commits, configuration logging, or local disk inspection.
  * *Benefit*: Keeps secrets out of repository files; credentials are loaded directly into application memory.
* **KMS SSE-KMS Encryption**:
  * *Threat Mitigated*: Physical drive theft from AWS datacenters or unauthorized access to raw S3 storage blocks.
  * *Benefit*: Encrypts patient records at rest using cryptographic keys with restricted IAM access policies.
* **S3 Private Access & CloudFront OAC**:
  * *Threat Mitigated*: Direct access to document storage and frontend static storage, scraping of S3 endpoints, and unauthenticated downloads.
  * *Benefit*: Restricts S3 object downloads, forcing static web requests through CloudFront and diagnostic file access through backend pre-signed URLs.
* **VPC Endpoints**:
  * *Threat Mitigated*: Interception of API traffic on the public internet, man-in-the-middle attacks, and network route hijacking.
  * *Benefit*: Routes all AWS API calls within AWS's physical network, keeping traffic off the public internet.
* **HTTPS/TLS Enforced**:
  * *Threat Mitigated*: Eavesdropping and traffic sniffing of sensitive patient records and JWT authorization headers.
  * *Benefit*: Encrypts all user traffic in transit between the client browser, CloudFront, and the ALB.

### 5. Architecture Diagram Validation

The current ASCII diagram in [ARCHITECTURE.md](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/docs/aws/ARCHITECTURE.md) is **technically incorrect** and **does not match the actual Terraform implementation**. It reflects the legacy, manual single-node deployment.

**Missing Components in Current Diagram**:
* No VPC, subnets (Public, Private, Database), or Availability Zones shown.
* Missing Application Load Balancer (ALB) and Auto Scaling Group (ASG).
* Missing CloudFront CDN distribution and its Origin Access Control (OAC) setup.
* Missing Route53 DNS zones.
* Missing NAT Gateway.
* Missing VPC Endpoints (SSM, Secrets Manager, S3 Gateway).
* Missing RDS MySQL service (shows an EC2 instance for MySQL instead).

**Incorrect Traffic Flows**:
* *Internet → Frontend EC2*: In Terraform, frontend traffic routes through Route53 → CloudFront → S3 (Frontend).
* *Frontend EC2 → Backend EC2*: In Terraform, the client browser makes API requests directly to Route53 → ALB → Backend EC2 ASG nodes in private subnets.
* *Backend EC2 → Database EC2*: In Terraform, backend EC2 instances connect to the managed RDS MySQL instance in the database subnets, not a database on an EC2 instance.
* *Backend EC2 → S3 (direct)*: In Terraform, S3 requests are routed privately through the S3 VPC Gateway Endpoint, which is not represented.

---

## Deliverable 1: Slide-by-Slide Presentation Structure

* **Target Audience**: Technical Reviewers / Infrastructure Engineers
* **Presentation Focus**: Terraform Architecture (55%), AWS Infrastructure Design (30%), Application Flow Context (15%)

---

### Slide 1: Title Slide & Review Overview
* **Slide Title**: Infrastructure & Terraform Architecture Review
* **Subtitle**: Automated, High-Availability Patient & Document Management System
* **Slide Objective**: Introduce the presentation, set technical expectations, and establish the review goals.
* **Key Talking Points**:
  * Overview of the platform: moving from legacy host-based setup to modern automated IaC.
  * Review scope: networking, security, data isolation, and Terraform code quality.
  * Target audience: technical reviewers validating production-readiness.
* **Visuals Required**: Clean layout with a minimalist engineering theme, showing the conversation ID and date.
* **Speaker Notes**:
  > "Welcome to the engineering review for the Patient Management System. Today we will focus on how we transitioned a legacy host-based application into a highly secure, automated AWS environment using Terraform. We'll inspect network topology, security controls, Terraform modular patterns, and bootstrapping mechanisms. Our goal is to evaluate production readiness and outline gaps for remediation."

---

### Slide 2: Application Context & Executive Summary
* **Slide Title**: Application Context & Business Flow
* **Slide Objective**: Provide business context using the requested executive summary statement.
* **Key Talking Points**:
  * "A secure patient and medical document management platform that enables healthcare professionals to manage patient information and securely store associated documents."
  * Target users: Clinic administrators and medical professionals.
  * Primary actions: Patient metadata indexing (MySQL) and medical diagnostic upload (S3).
  * Architecture transition: Moving from manual host setup to automated multi-tier architecture.
* **Visuals Required**: Simple high-level flowchart showing: Healthcare Professional → JWT Authenticated Request → Metadata (RDS) / Documents (S3).
* **Speaker Notes**:
  > "Before diving into the Terraform code, let's establish the context. The application is a secure patient and medical document management platform for healthcare professionals. Its core business flows are simple: managing patient files and records. However, because it handles sensitive medical data, the underlying infrastructure must prioritize strict data isolation, encryption, and zero public exposure of databases or application servers."

---

### Slide 3: Deployed AWS Production Architecture
* **Slide Title**: Target AWS Infrastructure Topology
* **Slide Objective**: Present the complete end-to-end AWS resource layout.
* **Key Talking Points**:
  * DNS routing via Route53 pointing subdomains to ALB and root domain to CloudFront.
  * Global frontend delivery using CloudFront (with OAC) and S3 static hosting.
  * High-availability backend using an ALB and Auto Scaling Group across private subnets.
  * Isolated database tier running managed AWS RDS MySQL.
  * Cryptographic security via KMS Customer Managed Keys and Secrets Manager.
* **Visuals Required**: Modern AWS architecture diagram highlighting public, private, and database subnet boundaries across two Availability Zones.
* **Speaker Notes**:
  > "This diagram represents the actual infrastructure deployed by the Terraform codebase. Traffic enters via Route53. Static assets are served globally via CloudFront from a private S3 bucket using Origin Access Control. API calls are sent to an Application Load Balancer, which routes traffic to backend EC2 instances inside private subnets. The database is hosted on a managed RDS instance inside dedicated database subnets. The architecture ensures that no backend compute node or database is directly accessible from the public internet."

---

### Slide 4: Networking & Subnet Segmentation
* **Slide Title**: VPC Topology & Network Segmentation
* **Slide Objective**: Explain the network architecture and CIDR layout.
* **Key Talking Points**:
  * VPC IP allocation: `10.0.0.0/16` CIDR block.
  * Subnet division across 2 AZs: Public (`10.0.1.0/24`, `10.0.2.0/24`), Private (`10.0.11.0/24`, `10.0.12.0/24`), Database (`10.0.21.0/24`, `10.0.22.0/24`).
  * Outbound transit: Single NAT Gateway in public subnets allowing outbound internet access for private hosts.
  * Private VPC Endpoints: Interface endpoints for SSM, SSMMessages, EC2Messages, Secrets Manager, and a Gateway endpoint for S3.
* **Visuals Required**: Subnet nesting diagram highlighting VPC CIDR and IP distribution.
* **Speaker Notes**:
  > "We've split the VPC into three distinct tiers across two Availability Zones. The public subnet hosts the ALB. The private subnet hosts the application nodes, which don't have public IPs. The database subnet hosts the RDS instance. To allow our private nodes to communicate with AWS services without traversing the public internet, we deployed interface and gateway endpoints. This keeps internal API calls off the public internet, reducing exposure to traffic sniffing and routing attacks."

---

### Slide 5: High Availability Backend & Compute Tier
* **Slide Title**: Compute Tier: ALB & Auto Scaling Groups
* **Slide Objective**: Explain how backend scaling, load balancing, and health checks operate.
* **Key Talking Points**:
  * Application Load Balancer in public subnets distributing HTTP/HTTPS traffic.
  * Auto Scaling Group (ASG) running inside private subnets (Min: 1, Max: 2, Desired: 1).
  * ELB Health Check configuration: active requests to `/health` (expected `200 OK`, 30s interval).
  * Rolling update deployment strategy using `instance_refresh` with `create_before_destroy` lifecycle rules.
* **Visuals Required**: High-availability flow showing ALB routing to healthy ASG nodes across AZ-1 and AZ-2.
* **Speaker Notes**:
  > "The compute tier uses an Auto Scaling Group deployed in private subnets. Traffic is distributed by the ALB. The ALB performs active HTTP health checks on the path `/health` on port 8000. If an instance becomes unhealthy, the ASG terminates it and provisions a new one. During deployments, we use Terraform's instance refresh block to perform rolling updates, maintaining a minimum of 50% healthy capacity."

---

### Slide 6: Managed Database Tier
* **Slide Title**: Database Tier: Managed AWS RDS MySQL
* **Slide Objective**: Explain the database configurations and security boundaries.
* **Key Talking Points**:
  * Managed RDS MySQL engine version 8.4 (db.t3.micro).
  * Isolated database subnet group (`module.vpc.database_subnet_group_name`).
  * Security group limits database access strictly to the backend EC2 security group on port 3306.
  * Automated backup retention configured for 7 days with deletion protection.
* **Visuals Required**: Database isolation diagram showing DB Subnet Group blocking public access and accepting only mysql-tcp (3306) from the Backend SG.
* **Speaker Notes**:
  > "Unlike the legacy architecture which ran MySQL on a self-managed EC2 instance, the Terraform configuration provisions a managed AWS RDS MySQL database. This offloads patching and backups. The RDS instance has public accessibility disabled and is placed in the database subnets. Security group rules block all ingress to port 3306 unless it originates from the backend application instances."

---

### Slide 7: Global Frontend Distribution
* **Slide Title**: Serverless Frontend: S3 & CloudFront OAC
* **Slide Objective**: Detail the hosting architecture for the React SPA.
* **Key Talking Points**:
  * Transition from host-based Nginx to S3 static hosting + CloudFront CDN.
  * Public access on S3 frontend bucket blocked completely.
  * Origin Access Control (OAC) enforcing that S3 objects are only read via the CloudFront distribution.
  * Single Page Application (SPA) routing support: Custom error rules routing 403/404 errors to `/index.html` with a 200 OK response.
* **Visuals Required**: Traffic flow diagram: User Browser → Route53 → CloudFront (OAC) → S3 (Frontend Bucket).
* **Speaker Notes**:
  > "For the frontend, we moved away from VM-hosted Nginx. We host the compiled React assets in a private S3 bucket and distribute them globally via CloudFront. To secure the bucket, we use Origin Access Control. This ensures users cannot bypass CloudFront to download files directly from S3. To support client-side routing in React, we configured custom error responses that rewrite 403 and 404 errors to index.html with a 200 status code."

---

### Slide 8: Terraform Architecture & Modular Design
* **Slide Title**: Terraform Codebase & Directory Structure
* **Slide Objective**: Analyze the organization and modularity of the Terraform configuration.
* **Key Talking Points**:
  * Project-specific local modules under `modules/`: `kms`, `secrets`, `s3`, `security-groups`, `iam`, `rds`, `launch-template`, `asg`, `frontend`, `dns`.
  * Input parameterization using `variables.tf` and `terraform.tfvars`.
  * Resource output mappings (`outputs.tf`) allowing modular data sharing.
  * Dependency injection: database endpoint and S3 bucket names dynamically feed the secrets module.
* **Visuals Required**: Folder directory structure diagram or dependency flow mapping between modules.
* **Speaker Notes**:
  > "The Terraform codebase is structured around modular design principles. Instead of writing a single flat main.tf file, we divided the infrastructure into 10 local modules. This makes the code readable and maintainable. We inject inputs using variables and pass outputs between modules. For example, the RDS database endpoint is only known after creation, so we pass it dynamically to the Secrets module to configure the application's runtime credentials."

---

### Slide 9: Infrastructure as Code Patterns
* **Slide Title**: Core IaC Concepts and Patterns Demonstrated
* **Slide Objective**: Highlight technical Terraform concepts used in the repository.
* **Key Talking Points**:
  * *Modular design*: Enforcing encapsulation and boundaries between resources.
  * *Dynamic lookups*: Fetching Ubuntu AMIs using Canonical filter tags.
  * *Dependency chaining*: Orchestrating build order (KMS key must exist before S3 encryption; RDS must exist before secrets).
  * *Environment separation*: Decoupling variable defaults from active environments via tfvars.
  * *Composition*: Assembling community modules (VPC) with custom-tailored modules.
* **Visuals Required**: List of Terraform keywords mapped to code snippets (e.g. `data`, `module`, `depends_on`, `output`).
* **Speaker Notes**:
  > "This project demonstrates several advanced IaC patterns. We utilize dynamic data lookups to retrieve the latest Ubuntu 22.04 AMI at runtime. We use resource composition, joining the community VPC module with our custom launch templates and security groups. By passing outputs between modules, Terraform compiles the dependency graph automatically, ensuring that resources like the database are online before the configuration secrets are stored."

---

### Slide 10: Security Controls: Network & Compute
* **Slide Title**: Security Controls: Ingress & Compute Isolation
* **Slide Objective**: Detail the security design protecting compute and network tiers.
* **Key Talking Points**:
  * Private Subnets: Compute nodes have no public IP addresses and cannot receive public traffic.
  * Ingress controls: Security groups limit ALB access to ports 80/443, and Backend access to port 8000 from the ALB security group.
  * IAM Least Privilege: EC2 instance profile role attached via launch templates, granting permissions to S3, KMS, and Secrets Manager without AWS Access Keys.
  * VPC interface endpoints ensuring all system administration (SSM) traffic remains on the private AWS network.
* **Visuals Required**: Security mapping matrix showing Control → Threat Mitigated → Benefit.
* **Speaker Notes**:
  > "Security is implemented in depth. Because the compute instances run in private subnets with no public IPs, they are immune to direct public scans. We've applied micro-segmentation using security groups, allowing the backend to accept connections only from the ALB. Instead of baking long-lived AWS keys into the instances, we use IAM roles and instance profiles. This grants short-lived permissions to access S3 and Secrets Manager, mitigating credential leakage risks."

---

### Slide 11: Security Controls: Encryption & Secrets
* **Slide Title**: Security Controls: KMS & Secret Management
* **Slide Objective**: Explain the encryption-at-rest and credential protection strategies.
* **Key Talking Points**:
  * S3 Server-Side Encryption (SSE-KMS) using a Customer Managed Key (CMK) alias `patient-app-s3-key`.
  * Centralized secret storage using AWS Secrets Manager for DB credentials, JWT signing keys, and bucket parameters.
  * Dynamically loaded secrets: the backend application fetches credentials in-memory at startup via boto3, leaving no local disk footprint.
  * JWT (JSON Web Tokens) with a 24-hour expiration for patient endpoint authentication.
* **Visuals Required**: Diagram illustrating the dynamic secret fetching process at application startup.
* **Speaker Notes**:
  > "Encryption-at-rest is enforced using SSE-KMS with a customer-managed key. All document uploads are encrypted immediately on receipt by S3. Secrets Manager holds database hostnames, usernames, passwords, and the JWT signing key. At boot time, the backend calls Secrets Manager, loads these credentials into memory, and establishes database connections. This ensures that no passwords exist on disk or in the codebase."

---

### Slide 12: Deployment & Node Bootstrapping
* **Slide Title**: Automated Compute Bootstrapping
* **Slide Objective**: Outline how the Launch Template user-data automates backend deployments.
* **Key Talking Points**:
  * Launch Template runs a custom bash bootstrap script (`user-data.sh.tftpl`) at launch.
  * Updates package indexes and installs system dependencies (`git`, `python3-venv`, `python3-pip`).
  * Clones the configured git repository (`git_repo_url`) and checks out the deployment tag (`git_tag`).
  * Creates a Python virtual environment and installs PIP dependencies plus Gunicorn.
  * Injects runtime environment overrides (`AWS_SECRET_NAME`, `AWS_DEFAULT_REGION`) and starts the systemd service.
* **Visuals Required**: Timeline block diagram representing the boot sequence of an EC2 backend node.
* **Speaker Notes**:
  > "The deployment is automated using EC2 user data in the Launch Template. When an instance is launched by the ASG, it updates apt packages, installs git and python3-venv, and clones the repository. It checks out the specified git tag, builds a virtual environment, installs dependencies, and copies the systemd service file. We inject the target secret ARN and region, then start the systemd service. The database tables are automatically generated by the SQLAlchemy ORM during startup."

---

### Slide 13: Architectural Inconsistencies & Gaps
* **Slide Title**: Day-0 Audit: Documentation vs. Code Mismatches
* **Slide Objective**: Explicitly call out the critical gaps between the manuals and the Terraform files.
* **Key Talking Points**:
  * *Frontend mismatch*: Manual guide uses a frontend EC2 instance; Terraform uses S3 + CloudFront (leaving the bucket empty and missing a build/sync script).
  * *Database mismatch*: Manual guide installs MySQL on EC2; Terraform deploys a managed RDS MySQL service.
  * *Proxy mismatch*: Manual guide configures local Nginx reverse proxies on EC2; Terraform routes traffic directly from the ALB to Gunicorn on port 8000.
  * *Rebuild Lock*: Secrets Manager deletion lock prevents immediate redeployment during `destroy/apply` cycles.
* **Visuals Required**: Side-by-side comparison table showing: Documentation (EC2 Frontend, EC2 MySQL, local Nginx) vs. Terraform (S3/CloudFront, RDS MySQL, direct ALB routing).
* **Speaker Notes**:
  > "Our audit identified several critical inconsistencies between the manual guides and the Terraform code. The documentation instructs the user to configure a frontend EC2 instance and a self-managed database. In contrast, the Terraform code deploys S3, CloudFront, and RDS. Because of this, the frontend S3 bucket remains empty post-deployment. We've marked this as a NO-GO state for day-0 deployments until build scripts and documents are updated."

---

### Slide 14: Engineering Recommendations
* **Slide Title**: Remediation & Operational Roadmap
* **Slide Objective**: Outline concrete engineering steps to solve these mismatches.
* **Key Talking Points**:
  * **Enable Force Destroy**: Add `force_destroy = true` to both S3 buckets to prevent destroy failures when files are present.
  * **Add Random Suffix to Secrets**: Prevent Secrets Manager name collisions by appending dynamic resource suffixes.
  * **Automate Frontend Sync**: Create a local script (`deploy-frontend.sh`) to build the React application and upload static assets using Terraform outputs.
  * **Update Documentation**: Rewrite `DEPLOYMENT.md` to align with the S3 + CloudFront + RDS architecture.
* **Visuals Required**: Ordered checklist of the recommended engineering actions.
* **Speaker Notes**:
  > "To reach a GO state, we recommend implementing four improvements. First, add force destroy to the S3 modules. Second, append a random suffix to the secret name to allow instant rebuilds. Third, write a simple script that compiles the React application and uploads it to the newly created S3 bucket. Finally, we must rewrite the deployment documentation so that it accurately reflects the modern architecture defined by our Terraform code. Thank you, I am ready for questions."

---

## Deliverable 2: Gamma AI Prompt

```text
Create a highly professional, technical, reviewer-oriented engineering presentation reviewing the infrastructure and Terraform architecture of the "Patient Management System". The presentation must focus primarily on AWS cloud architecture, security controls, and Terraform implementation patterns rather than product features or healthcare topics.

Tone: Professional, analytical, technical, minimal marketing language.

Presentation Structure (12-14 slides):
1. Title Slide: Infrastructure & Terraform Architecture Review (Patient Management System - Automated, High-Availability Deployment)
2. Application Context: Brief summary of the app as "A secure patient and medical document management platform that enables healthcare professionals to manage patient information and securely store associated documents" detailing its core data and storage flows.
3. AWS Production Architecture: Showcase the global architecture featuring Route53, CloudFront CDN, S3, Application Load Balancers, Auto Scaling Groups, and RDS.
4. Network Design: Details of the VPC subnetting strategy (Public, Private, and Database subnets across 2 Availability Zones), NAT Gateway usage, and Private VPC Endpoints (Interface and Gateway endpoints for SSM, Secrets Manager, and S3).
5. High Availability Compute: Deep dive into the ALB and ASG setup in private subnets, Launch Templates, instance refresh, and active HTTP /health checks on port 8000.
6. Database Tier: Review of the managed AWS RDS MySQL 8.4 engine configuration in database-private subnets, security group rules limiting port 3306 ingress to the backend EC2 tier, and deletion protection policies.
7. Serverless Frontend: Contrast VM-hosted Nginx with S3 Static Web Hosting + CloudFront Origin Access Control (OAC), detailing SPA routing configuration (403/404 page overrides to index.html).
8. Terraform Modular Design: Structural review of modular components (kms, secrets, s3, security-groups, iam, rds, launch-template, asg, frontend, dns), parameterization using variables, and outputs.
9. Advanced IaC Patterns: Technical review of Terraform features demonstrated including dynamic data lookups (Ubuntu AMI, Route53 zones), dependency chaining, dynamic secret injection, and state-driven provisioning.
10. Security Controls (Network & Compute): Map controls to threats (Private Subnets, Security Groups, IAM Instance Profiles with Least Privilege) and their operational benefits.
11. Security Controls (Data & Secrets): Detailed review of KMS Customer Managed Key encryption for S3, AWS Secrets Manager credentials storage, and dynamic startup secrets retrieval.
12. Node Bootstrapping & User Data: Inspect the Launch Template user-data bootstrap script (apt setup, repository clone, git tag checkout, virtualenv configuration, and systemd service creation).
13. Architectural Inconsistencies & Day-0 Audit: Crucial slide highlighting mismatches between manual EC2 guides (which instruct building EC2-based frontends and local Nginx proxies) and the actual Terraform code (which deploys CloudFront/S3 and RDS), resulting in an empty frontend bucket blocker.
14. Remediation Roadmap: Checklist for operational readiness (adding S3 force_destroy, Secrets Manager naming suffix, automated frontend build/sync scripts, and updating deployment guides).
```

---

## Deliverable 3: Claude PPT Prompt

```text
You are a Staff Infrastructure Architect. Generate the content and presenter notes for a 14-slide engineering review deck focusing on the "Patient Management System" infrastructure. The primary focus is Terraform implementation, AWS cloud design, and security engineering. Avoid any marketing or generic healthcare product language.

Format each slide clearly with:
- [SLIDE TITLE]
- [SLIDE TEXT] (Concise, technical bullet points using specific AWS and Terraform terms)
- [VISUAL SUGGESTION] (Specific suggestions for diagrams, tables, or code blocks)
- [SPEAKER NOTES] (Detailed professional commentary explaining the rationale, security implications, and design choices)

Use the following slide-by-slide structure:

Slide 1: Title Slide
- Title: Infrastructure & Terraform Architecture Review
- Subtitle: Highly-Available, Private VPC Deployment of the Patient Management System
- Text: Technical review of network architecture, security controls, and IaC patterns.

Slide 2: Application Context & Metadata Flows
- Text: Secure patient metadata tracking (FastAPI + Gunicorn) and diagnostic file storage (S3). JWT authentication with per-user data isolation.
- Visual: Flowchart showing React client -> JWT -> Backend -> RDS/S3.

Slide 3: AWS Production Topology
- Text: Overview of the AWS topology. Route53, CloudFront CDN, S3, ALB, ASG, RDS, KMS, Secrets Manager.
- Visual: 3-tier AZ architecture diagram layout.

Slide 4: VPC Topology & Subnet Segmentation
- Text: VPC CIDR 10.0.0.0/16. Dual-AZ subnets (Public, Private, Database). NAT Gateway. Private VPC Interface Endpoints (SSM, Secrets Manager) and S3 Gateway Endpoint.
- Visual: Table of CIDR blocks, subnets, and routing table associations.

Slide 5: High-Availability Compute (ALB & ASG)
- Text: ASG in private subnets behind public ALB. HTTP target group on port 8000. ELB health check at /health. ASG rolling update with instance refresh.
- Visual: Flow showing ALB forwarding traffic to backend nodes in private subnets.

Slide 6: Managed RDS Database Tier
- Text: AWS RDS MySQL 8.4 engine. Dedicated DB subnets. Ingress restricted to Backend SG on port 3306. Backup retention and deletion protection.
- Visual: DB SG rule configuration table showing source security group mappings.

Slide 7: Serverless Frontend Distribution
- Text: S3 bucket (public access blocked) + CloudFront CDN + Origin Access Control (OAC). SPA routing (403/404 errors redirected to index.html with 200 OK).
- Visual: Comparison of Host-Based Nginx vs. S3+CloudFront.

Slide 8: Terraform Codebase Organization
- Text: Reusable modules (vpc, kms, s3, rds, asg, frontend, etc.). Environment separation via tfvars. Dependency management and output wiring.
- Visual: Directory structure map.

Slide 9: Infrastructure as Code Patterns
- Text: Dynamic data lookups (Ubuntu AMI, Route53 zone). Implicit/explicit dependency management. Dynamic resource references.
- Visual: Code snippet examples of data blocks and module inputs.

Slide 10: Security Controls: Network & Compute
- Text: Private subnets blocking public access. Security group micro-segmentation. IAM instance profiles with least-privilege policies. AmazonSSMManagedInstanceCore for secure console access.
- Visual: Grid mapping Control -> Threat Mitigated -> Benefit.

Slide 11: Security Controls: Encryption & Secrets
- Text: SSE-KMS with Customer Managed Key. Secrets Manager for database hostnames and JWT keys. Dynamic startup secrets retrieval.
- Visual: Secret retrieval flow diagram.

Slide 12: Automated Node Bootstrapping
- Text: Launch Template user-data shell script. Git clone and branch checkout. Virtualenv creation and pip dependency installation. Systemd config binding Gunicorn to 0.0.0.0:8000.
- Visual: Node bootstrap workflow timeline.

Slide 13: Technical Inconsistencies & Day-0 Audit
- Text: Mismatch between EC2-based manual docs and S3/CloudFront/RDS Terraform configurations. Empty S3 frontend bucket. Secrets Manager recreation lock. Missing S3 force_destroy.
- Visual: Side-by-side comparison table of documentation vs. Terraform.

Slide 14: Recommended Operational Roadmap
- Text: Configure force_destroy = true. Append dynamic suffixes to secrets. Create deploy-frontend.sh for React build and S3 upload. Rewrite DEPLOYMENT.md.
- Visual: Ordered action-item checklist.
```

---

## Deliverable 4: draw.io Architecture Diagram Prompt

```text
Generate a professional, production-grade AWS Architecture Diagram in draw.io (or similar tool) for a highly secure, multi-tier deployment of the Patient Management System. Use official AWS architecture icons and a clean, technical layout without unnecessary decorations.

Layout Elements & Boundaries:
1. Outer Boundary: "AWS Cloud"
2. Inside AWS Cloud:
   - "AWS Route53" (placed at the top-left ingress)
   - "AWS CloudFront CDN" (placed at top-middle, fronting the S3 frontend origin)
   - "AWS S3: Frontend Assets Bucket" (private, public access blocked, linked to CloudFront via an arrow labeled "OAC (Origin Access Control)")
   - A main boundary box: "VPC (CIDR: 10.0.0.0/16)" containing:
     - "Internet Gateway" (attached to the VPC boundary)
     - "NAT Gateway" (placed inside a Public Subnet)
     - "VPC Interface Endpoints" box (containing endpoints for SSM, SSMMessages, EC2Messages, Secrets Manager)
     - "VPC Gateway Endpoint" (S3)
     - Two horizontal or vertical boxes for Availability Zones: "Availability Zone 1 (us-east-1a)" and "Availability Zone 2 (us-east-1b)"
3. Subnet Layout inside each Availability Zone:
   - "Public Subnet (10.0.1.0/24 & 10.0.2.0/24)": Contains the "Application Load Balancer (ALB)" spanning both zones.
   - "Private Subnet (10.0.11.0/24 & 10.0.12.0/24)": Contains the "Auto Scaling Group (ASG)" containing "Backend EC2 Instance (FastAPI / Gunicorn)" in each zone.
   - "Database Subnet (10.0.21.0/24 & 10.0.22.0/24)": Contains the "AWS RDS MySQL Instance" in the database tier.
4. Security & Cryptography services (placed outside the VPC but inside AWS Cloud):
   - "AWS Secrets Manager" (storing credentials)
   - "AWS KMS (Customer Managed Key)" (linked to S3 buckets and IAM)
   - "AWS IAM Instance Profile" (attached to Backend EC2 instances)
   - "AWS S3: Patient Documents Bucket" (private, encrypted with SSE-KMS)

Traffic & Data Flow Arrows:
1. Public Web Traffic (Frontend):
   - User Browser -> Route53 (DNS query)
   - User Browser -> CloudFront (HTTPS request)
   - CloudFront -> S3 Frontend Assets Bucket (OAC read, GetObject)
2. Public API Traffic (Backend):
   - User Browser -> Route53 (DNS query)
   - User Browser -> ALB (HTTPS traffic on port 443)
   - ALB -> Backend EC2 ASG Instances (HTTP port 8000, private subnets)
3. Internal Backend Flows:
   - Backend EC2 -> Secrets Manager (fetch database host & credentials via VPC Interface Endpoint)
   - Backend EC2 -> RDS MySQL (SQL connection on port 3306 in Database Subnet, authorized by Security Groups)
   - Backend EC2 -> KMS (decrypt/generate data key for document uploads/reads)
   - Backend EC2 -> S3 Patient Documents Bucket (via S3 VPC Gateway Endpoint, reads/writes objects and generates pre-signed URLs)
4. Document Access Flow:
   - User Browser -> Backend EC2 (Request document view URL)
   - Backend EC2 -> S3 Patient Documents Bucket (Generate pre-signed URL)
   - Backend EC2 -> User Browser (Return pre-signed URL with 1-hour TTL)
   - User Browser -> S3 Patient Documents Bucket (Fetch document directly from S3 using the pre-signed URL)
```
