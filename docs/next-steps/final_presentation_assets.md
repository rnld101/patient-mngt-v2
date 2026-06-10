# Final Infrastructure Review & Presentation Assets

This document contains the final revised set of assets for the infrastructure and Terraform architecture review of the Patient Management System. 

All content has been re-aligned to the final requested weightage:
* **Terraform**: 70%
* **AWS Services & Architecture**: 25%
* **Application Context**: 5%

Slide count is strictly capped at **10 slides**, and all legacy EC2 database/frontend references, Day-0 audits, and migration details have been removed in favor of the current Terraform-managed production architecture.

---

## Deliverable 1: Updated Architecture Validation Report

The target production architecture has been reconciled against the codebase and validated according to the following architectural corrections:

1. **DNS Entry Point (Route53 Flow) [VALIDATED]**:
   * *Correction*: Traffic enters via Route53 DNS, resolving apex domain requests (`lavenbloom.xyz`) directly to the CloudFront distribution, and API subdomain requests (`api.lavenbloom.xyz`) directly to the Application Load Balancer (ALB).
   * *Implementation*: Verified in the `dns` and `frontend` modules. Custom domain aliases point to the correct regional AWS endpoints.
2. **S3 Gateway Endpoint Placement [VALIDATED]**:
   * *Correction*: The S3 Gateway Endpoint is a VPC route-table resource and resides strictly inside the VPC boundary.
   * *Implementation*: Verified in `terraform/main.tf` (`aws_vpc_endpoint.s3`). It links to both the public and private route tables, routing S3-destined traffic privately within the VPC.
3. **KMS & S3 Server-Side Encryption [VALIDATED]**:
   * *Correction*: The backend application does not perform client-side encryption. The backend writes files directly to S3 via the Gateway Endpoint, and S3 handles Server-Side Encryption (SSE-KMS) transparently using the Customer Managed Key (`patient-app-s3-key`).
   * *Implementation*: Verified in the `iam`, `s3`, and `kms` modules. The backend role requires `kms:GenerateDataKey` and `kms:Decrypt` permissions to permit S3 to perform cryptographic operations.
4. **NAT Gateway Representation [VALIDATED]**:
   * *Correction*: The NAT Gateway resides inside a public subnet and is explicitly shown. Private subnets route outbound traffic through it for package downloading, git cloning, and updates during bootstrapping.
   * *Implementation*: Verified in the `vpc` module parameters (`enable_nat_gateway = true` and `single_nat_gateway = true`).
5. **Multi-AZ Representation [VALIDATED]**:
   * *Correction*: The Auto Scaling Group (ASG) spans multiple Availability Zones. The architecture explicitly diagrams Availability Zone A (with Private Subnet A and Backend EC2 A) and Availability Zone B (with Private Subnet B and Backend EC2 B).
   * *Implementation*: Verified in the `vpc` and `asg` modules. Subnets span `us-east-1a` and `us-east-1b`, and the ASG consumes the private subnet ID list.

---

## Deliverable 2: Updated draw.io Architecture Diagram Prompt

```text
Generate a professional, clean AWS Architecture Diagram in draw.io for a highly secure, multi-tier deployment of the Patient Management System. Use official AWS icons and keep layout minimal and technical.

Layout Boundaries & Resource Placement:
1. Outer Boundary: "AWS Cloud"
2. Inside AWS Cloud:
   - "AWS Route53" (DNS Entry Point, placed at the top-left ingress)
   - "AWS CloudFront CDN" (placed at top-middle)
   - "AWS S3: Frontend Assets Bucket" (Private S3 origin, OAC enabled)
   - A main boundary box: "VPC (CIDR: 10.0.0.0/16)" containing:
     - "Internet Gateway" (attached to VPC border)
     - "VPC Gateway Endpoint (S3)" (placed inside the VPC border, connected to route tables)
     - "VPC Interface Endpoints" box (SSM, Secrets Manager, EC2Messages)
     - Two Availability Zone boxes: "Availability Zone A (us-east-1a)" and "Availability Zone B (us-east-1b)"
3. Subnet Segments inside the AZs:
   - "Public Subnets (10.0.1.0/24 & 10.0.2.0/24)": Contains the "Application Load Balancer (ALB)" (spans both AZs) and a "NAT Gateway" (placed in AZ A's public subnet).
   - "Private Subnets (10.0.11.0/24 & 10.0.12.0/24)": Contains the "Auto Scaling Group (ASG)" spanning both zones. Inside AZ A: "Backend EC2 Instance A". Inside AZ B: "Backend EC2 Instance B" (both t3.micro, running FastAPI, port 8000, no public IP).
   - "Database Subnets (10.0.21.0/24 & 10.0.22.0/24)": Contains the "Managed AWS RDS MySQL Instance" (spans both AZs for multi-AZ, or primary in AZ A).
4. Out-of-VPC Security Services (but inside AWS Cloud):
   - "AWS Secrets Manager" (dynamic credentials store)
   - "AWS KMS (Customer Managed SSE-KMS Key)"
   - "AWS S3: Patient Documents Bucket" (Private, SSE-KMS encryption enabled)

Traffic & Connection Flows (Draw directional arrows):
1. DNS Flow:
   - Users -> Route53 (Query DNS)
   - Route53 -> lavenbloom.xyz (alias points to CloudFront CDN)
   - Route53 -> api.lavenbloom.xyz (alias points to ALB)
2. Frontend HTTPS Flow:
   - Users -> CloudFront CDN (HTTPS)
   - CloudFront CDN -> S3 Frontend Assets Bucket (OAC read, GetObject)
3. API HTTPS Flow:
   - Users -> ALB (HTTPS port 443)
   - ALB -> Backend EC2 ASG Instances (HTTP port 8000, private subnets)
4. Outbound Bootstrap Transit:
   - Backend EC2 Instances -> NAT Gateway (outbound package downloads via IGW) -> Internet
5. Private Data & AWS API Flows:
   - Backend EC2 -> VPC Interface Endpoints -> Secrets Manager (fetch credentials)
   - Backend EC2 -> RDS MySQL (Port 3306, DB SG allows only Backend SG)
   - Backend EC2 -> VPC Gateway Endpoint (S3) -> S3 Patient Documents Bucket (Write/Read objects)
   - S3 Patient Documents Bucket -> KMS (Automatic Server-Side Encryption / SSE-KMS)
```

---

## Deliverable 3: Slide-by-Slide Deck Outline (10 Slides Maximum)

---

### Slide 1: Title Slide
* **Slide Title**: Infrastructure & Terraform Architecture Review
* **Subtitle**: Automated, High-Availability Private VPC Deployment of the Patient Management System
* **Slide Objective**: Introduce the review session, target architecture, and Terraform scope.
* **Key Talking Points**:
  * Infrastructure as Code (IaC) review of the Patient Management System.
  * System goals: network-level isolation, high availability, database protection, and automated scaling.
  * Audit parameters: 100% Terraform-managed resources.
* **Visuals Required**: Clean layout with a dark minimalist engineering theme. Include project metadata.

---

### Slide 2: Application Context (5% Weightage)
* **Slide Title**: Application Context & Data Flows
* **Slide Objective**: Explain the application workflow briefly to contextualize the network and storage design.
* **Key Talking Points**:
  * Application: A secure patient and medical document management platform that enables healthcare professionals to manage patient information and securely store associated documents.
  * Security need: Patient records and diagnostic files require strict compliance, encryption, and per-user data isolation.
  * Document Flow: Client Browser → FastAPI Backend → Private S3 Bucket. Accessed securely via time-limited S3 pre-signed URLs (1-hour TTL).
* **Visuals Required**: Simplified horizontal flowchart showing: Browser → Backend API → S3 (Documents) / RDS (Metadata).

---

### Slide 3: Deployed AWS Production Architecture (25% Weightage)
* **Slide Title**: Production Target AWS Architecture
* **Slide Objective**: Present the complete validated AWS infrastructure design.
* **Key Talking Points**:
  * Entry Point: Route53 resolves subdomains, pointing web requests to CloudFront and API traffic to the ALB.
  * Edge Delivery: CloudFront CDN serving static React assets from a private S3 bucket via Origin Access Control (OAC).
  * Compute Tier: Public ALB routing traffic to a Multi-AZ Auto Scaling Group (EC2) inside private subnets.
  * Database & Storage: Managed RDS MySQL instance and KMS-encrypted private S3 document bucket.
* **Visuals Required**: Multi-AZ AWS architecture diagram illustrating subnet boundaries, Route53 resolution, and security groups.

---

#### Slide 4: Network Design & High Availability (25% Weightage)
* **Slide Title**: VPC Segmentation, High Availability & Routing
* **Slide Objective**: Detail the VPC subnet structure, routing pathways, and network endpoints.
* **Key Talking Points**:
  * Multi-AZ VPC (`10.0.0.0/16`) spanning `us-east-1a` and `us-east-1b`.
  * Subnet division: Public (ALB, NAT Gateway), Private (ASG EC2 nodes), and Database (RDS MySQL).
  * Outbound transit: Single NAT Gateway in public subnets enabling private nodes to query git/packages during bootstrapping.
  * Private Endpoints: VPC Interface Endpoints (SSM, Secrets Manager) and VPC Gateway Endpoint (S3) keeping system API traffic inside the VPC.
* **Visuals Required**: Subnet allocation table showing CIDR blocks, routing tables, and AZ locations.

---

#### Slide 5: Terraform Codebase Structure (70% Weightage)
* **Slide Title**: Terraform Codebase: Modular Design
* **Slide Objective**: Analyze the organization and modularity of the IaC code.
* **Key Talking Points**:
  * Strict folder structure segregating infrastructure into 10 encapsulated local modules under `modules/`.
  * Modular boundaries: `vpc`, `asg`, `rds`, `s3`, `iam`, `kms`, `secrets`, `launch-template`, `frontend`, `dns`.
  * Decoupled configuration: Variables (`variables.tf`) define inputs, and outputs (`outputs.tf`) expose resource attributes.
  * Reusable design: Main configuration acts as an orchestrator, wiring outputs to inputs to build dependencies.
* **Visuals Required**: Directory tree layout of the `terraform/` directory.

---

#### Slide 6: Terraform Features Demonstrated (70% Weightage)
* **Slide Title**: Terraform Design Patterns & IaC Concepts
* **Slide Objective**: Detail the advanced Terraform concepts demonstrated in the repository.
* **Key Talking Points**:
  * *Modularization*: Standardizes deployments by packaging networking, storage, compute, and security.
  * *Dynamic Data Sources*: Queries canonical Ubuntu AMIs and active Route53 public zones dynamically.
  * *Resource Composition*: Combines community modules (VPC, RDS, Security Groups) with custom-tailored S3 and IAM resources.
  * *State-driven Management*: State files compile resources and manage drift safely.
* **Visuals Required**: Table mapping Terraform features (Data Sources, Inputs, Composition, Graph, State) to specific locations in the project files.

---

#### Slide 7: Terraform Provisioning Workflow (70% Weightage)
* **Slide Title**: Infrastructure Orchestration & Dependency Resolution
* **Slide Objective**: Illustrate the dependency resolution pipeline of the Terraform apply workflow.
* **Key Talking Points**:
  * Dependency Graph: Terraform automatically determines resource apply order.
  * Pipeline Order: Networking (VPC) & Key Management (KMS) are created first.
  * Storage (S3) and Database (RDS) modules deploy next.
  * RDS endpoints and bucket names are passed to Secrets Manager; IAM policies inherit ARNs.
  * Launch Template and ASG consume subnet IDs, and ALB/CloudFront are built before Route53 DNS records bind.
* **Visuals Required**: Vertical flowchart representing the `terraform apply` step-by-step pipeline.

---

#### Slide 8: Automated Infrastructure & Bootstrapping (70% Weightage)
* **Slide Title**: Compute Automation: Launch Templates & User Data
* **Slide Objective**: Detail how compute provisioning and application deployment are automated.
* **Key Talking Points**:
  * Launch Templates enforce private network bindings (`associate_public_ip_address = false`) and attach IAM roles.
  * Node Bootstrapping: Launch template executes a custom bash script (`user-data.sh.tftpl`) at boot.
  * Deployment Automation: Updates apt packages, clones the git repository, and checks out the configured `git_tag`.
  * App Startup: Creates a python virtual environment, installs requirements, sets up systemd to bind Gunicorn to `0.0.0.0:8000`, and auto-heals via the ASG.
* **Visuals Required**: Code snippet of the user-data template execution sequence.

---

#### Slide 9: Security Architecture (70% Weightage)
* **Slide Title**: Security Engineering & Threat Mitigation
* **Slide Objective**: Map security controls to threat mitigation and operational benefits.
* **Key Talking Points**:
  * *VPC Isolation*: Compute & Database tiers reside in private subnets, blocking direct public entry.
  * *Micro-segmentation*: Security groups limit ALB ingress to 80/443, and database ingress to port 3306 from the Backend SG only.
  * *Credential Protection*: Secrets Manager keeps passwords out of git commits; loaded dynamically in-memory at startup.
  * *At-Rest Encryption*: S3 uses SSE-KMS default encryption with a Customer Managed Key.
  * *Origin Protection*: CloudFront uses Origin Access Control (OAC) to prevent direct S3 frontend bucket reads.
* **Visuals Required**: Grid showing: Security Control → Threat Mitigated → Operational Benefit.

---

#### Slide 10: Key Outcomes & Future Enhancements (70% Weightage)
* **Slide Title**: Infrastructure Outcomes & Future Roadmap
* **Slide Objective**: Summarize current achievements and present a roadmap for future infrastructure improvements.
* **Key Talking Points**:
  * Current Successes: High availability across AZs, complete IaC automation, zero-exposure database, and auto-scaling.
  * Future IaC Roadmap:
    * Migrating local state to S3 Remote State Backend with DynamoDB state locking.
    * Parameterizing multi-environment workspace structures (Dev, Staging, Prod).
    * Setting up CI/CD pipelines (GitHub Actions) for automatic terraform formatting, linting, and applying.
    * Integrating CloudWatch monitoring, alerting, and blue/green deployments.
* **Visuals Required**: Split-screen dashboard layout mapping Current Achievements vs. Future Roadmap.

---

## Deliverable 4: Slide Speaker Notes

> **Slide 1 Speaker Notes**: "Welcome to the infrastructure review for the Patient Management System. Today we will focus on our transition to a fully automated, high-availability AWS cloud environment managed entirely by Terraform. We will look at network design, compute scalability, serverless assets delivery, security segmentation, and bootstrapping automation. Our main goal is to review code quality and identify operational gaps."
>
> **Slide 2 Speaker Notes**: "To set the context, the application is a secure patient and medical document management platform for healthcare professionals. Because it handles personal health information, we must enforce data isolation at every layer. The application uses FastAPI, and all database queries filter by the user ID extracted from the JWT token. Documents are stored privately in S3 and accessed only via short-lived pre-signed URLs, preventing direct S3 path leaks."
>
> **Slide 3 Speaker Notes**: "This is the target production layout. Public DNS is managed in Route53. Frontend requests point to CloudFront, which pulls from a private S3 bucket. API requests go to an ALB, which routes traffic to private EC2 instances managed by an Auto Scaling Group. Secrets and database engines are completely private. This topology ensures that no application servers or databases are exposed directly to the public internet."
>
> **Slide 4 Speaker Notes**: "Networking is configured inside a custom VPC. We have segmented our network into Public, Private, and Database subnets across two Availability Zones. Outbound traffic from the private subnets goes through a NAT Gateway. To optimize cost and security, we deployed VPC interface endpoints for SSM and Secrets Manager, and a gateway endpoint for S3. This keeps our internal AWS API traffic off the public internet."
>
> **Slide 5 Speaker Notes**: "The Terraform codebase is structured into local modules under the modules directory. Each module acts as a standalone block, defining its own variables and outputs. In the root main.tf, we compose these modules, passing network parameters to compute modules, and database outputs to Secrets Manager. This modular design makes the code reusable and easy to test."
>
> **Slide 6 Speaker Notes**: "Terraform manages the resource dependency graph automatically. Resource composition allows us to pass dynamic parameters, like the RDS database endpoint, directly into the Secrets Manager module. Explicit dependencies are set using depends_on where needed, such as ensuring our KMS keys are fully active before S3 attempts to use them for default encryption."
>
> **Slide 7 Speaker Notes**: "The compute tier relies on an Application Load Balancer and an Auto Scaling Group. The ALB listens on port 443, handles SSL termination, and routes traffic to port 8000 on backend instances. The ASG maintains healthy instance counts in private subnets, performing rolling updates via instance refresh. The ALB target group monitors node health by polling the FastAPI health endpoint."
>
> **Slide 8 Speaker Notes**: "We automate node bootstrapping using EC2 user data in the Launch Template. When a node starts, it updates packages, installs git and python3-venv, and clones the repository. It checks out the specified git tag, builds a virtual environment, installs Gunicorn, and copies the systemd service file. Secret names are injected via environment overrides, and systemd starts the service."
>
> **Slide 9 Speaker Notes**: "We host the static React application using a private S3 bucket and CloudFront. Origin Access Control is enabled so that objects can only be read via CloudFront. To support React Router client-side navigation, we configured CloudFront custom error rules to rewrite 403 and 404 responses to index.html with a 200 OK status code, preventing page load errors."
>
> **Slide 10 Speaker Notes**: "In summary, the Terraform implementation provides a secure, high-availability architecture. However, we have defined a roadmap to mature our operations. This includes migrating our local state to an S3 bucket with DynamoDB state locking, setting up CI/CD pipelines to lint and run Terraform plans, and deploying CloudWatch logging and metrics dashboards to monitor node resource usage. Thank you, I am ready for questions."

---

## Deliverable 5: Updated Gamma AI Prompt

```text
Create a highly professional, technical, reviewer-oriented engineering presentation reviewing the infrastructure and Terraform architecture of the "Patient Management System". The presentation must represent the CURRENT Terraform-managed production architecture only, removing all legacy EC2-hosted database or frontend server references.

Tone: Professional, analytical, technical, minimal marketing language.
Target Slide Count: 10 Slides.
Weightage Focus: Terraform (70%), AWS Architecture (25%), Application Context (5%).

Slide-by-Slide Outline:
1. Title Slide: Infrastructure & Terraform Architecture Review (Patient Management System - Automated, High-Availability Deployment)
2. Application Context (5%): Core functionalities of the patient platform. Explain why patient records require secure S3 document storage (compliance/PHI) and the pre-signed URL workflow.
3. Production AWS Architecture (25%): Detailed overview of the target topology featuring Route53 (DNS entry point resolving apex domain to CloudFront and api subdomain to ALB), CloudFront CDN, S3, ALB, Auto Scaling Groups, and RDS.
4. Network Design & High Availability (25%): Subnet segmentation layout (VPC 10.0.0.0/16, Public/Private/DB subnets), NAT Gateway (for outbound bootstrap transit), and private VPC endpoints (Interface endpoints for SSM/Secrets Manager, and a S3 Gateway Endpoint placed inside the VPC boundary).
5. Terraform Codebase Structure (70%): Folder directory review of the root main.tf and its 10 local modules (vpc, kms, s3, rds, security-groups, iam, secrets, launch-template, asg, frontend, dns) showing inputs/outputs encapsulation.
6. Terraform Features Demonstrated (70%): In-depth look at Terraform IaC capabilities implemented: modules, variables, outputs, dynamic data sources, resource references, dependency graphs, and state-driven provisioning.
7. Terraform Provisioning Workflow (70%): Step-by-step infrastructure apply order determined by dependency resolution (VPC/KMS -> S3/RDS -> Secrets/IAM -> Launch Template -> ASG -> ALB -> CloudFront -> Route53).
8. Automated Infrastructure & Bootstrapping (70%): Compute tier automation using Launch Templates, user-data bootstrap bash scripts (git tag cloning, python virtualenv setup, systemd Gunicorn binding to 0.0.0.0:8000), and auto-healing through the ASG.
9. Security Architecture (70%): Detailed grid mapping Security Controls to Threats Mitigated and Benefits (VPC Private Subnets, SG micro-segmentation, Secrets Manager dynamic in-memory load, IAM roles, S3 SSE-KMS, CloudFront OAC, VPC Endpoints).
10. Key Outcomes & Future Enhancements (70%): Review current achievements (HA, IaC, auto-scaling) and present future roadmap (S3 Remote State with DynamoDB locking, multi-environment workspaces, CI/CD actions, CloudWatch monitoring).
```

---

## Deliverable 6: Updated Claude PPT Generation Prompt

```text
You are a Staff Infrastructure Architect. Generate the content and presenter notes for a 10-slide engineering review deck focusing on the "Patient Management System" infrastructure. The primary focus is Terraform implementation, AWS cloud design, and security engineering. Avoid any marketing or generic healthcare product language. Represent the CURRENT Terraform-managed production architecture only, removing all legacy EC2-hosted database or frontend server references.

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

Slide 2: Application Context (5% Weightage)
- Title: Application Context & Data Flows
- Text: Patient metadata tracking (FastAPI + Gunicorn) and diagnostic file storage (S3). PHI compliance requirements. Document upload/view flow via 1-hour expiry pre-signed URLs.
- Visual: Flowchart showing React client -> JWT -> Backend -> RDS/S3.

Slide 3: Production AWS Topology (25% Weightage)
- Title: Production Target AWS Architecture
- Text: Route53 DNS entry point (lavenbloom.xyz to CloudFront, api.lavenbloom.xyz to ALB). CloudFront CDN serving static files from private S3 bucket. ALB routing to ASG nodes in private subnets. Managed RDS MySQL, KMS, Secrets Manager.
- Visual: Multi-tier AZ architecture layout.

Slide 4: VPC Topology & Subnet Segmentation (25% Weightage)
- Title: VPC Segmentation, High Availability & Routing
- Text: VPC CIDR 10.0.0.0/16. Dual-AZ subnets (Public, Private, Database). NAT Gateway. Private VPC Interface Endpoints (SSM, Secrets Manager) and S3 Gateway Endpoint placed inside the VPC.
- Visual: Table of CIDR blocks, subnets, and routing table associations.

Slide 5: Terraform Codebase Structure (70% Weightage)
- Title: Terraform Codebase: Modular Design
- Text: Reusable modules (vpc, kms, s3, rds, security-groups, iam, secrets, launch-template, asg, frontend, dns). Input variables and output wiring. Reusable architecture composition.
- Visual: Directory tree map of the terraform/ directory.

Slide 6: Terraform Features Demonstrated (70% Weightage)
- Title: Terraform Design Patterns & IaC Concepts
- Text: Modular design patterns. Dynamic data sources (Ubuntu AMI, Route53 zone). Implicit/explicit dependency management. Dynamic resource references. State-driven provisioning.
- Visual: Code snippet examples of data blocks and module inputs.

Slide 7: Terraform Provisioning Workflow (70% Weightage)
- Title: Infrastructure Orchestration & Dependency Resolution
- Text: Step-by-step execution plan: Networking -> Security -> Storage -> Database -> Secrets -> Launch Template -> ASG -> ALB -> CloudFront -> Route53. How dependency graphs dictate order.
- Visual: Vertical flowchart representing the apply pipeline.

Slide 8: Compute Automation & Bootstrapping (70% Weightage)
- Title: Compute Automation: Launch Templates & User Data
- Text: Launch Template private network settings. User-data bootstrap script (system updates, git cloning tag v1.0.0, virtualenv, and Gunicorn service binding to 0.0.0.0:8000). Auto-healing via ASG.
- Visual: Node bootstrap workflow timeline.

Slide 9: Security Architecture (70% Weightage)
- Title: Security Engineering & Threat Mitigation
- Text: VPC private subnets blocking direct entry. Security group micro-segmentation. Secrets Manager dynamically loading secrets in-memory. S3 default SSE-KMS encryption. CloudFront OAC origin protection. VPC Endpoints.
- Visual: Matrix mapping Control -> Threat Mitigated -> Benefit.

Slide 10: Outcomes & Future Roadmap (70% Weightage)
- Title: Infrastructure Outcomes & Future Roadmap
- Text: Achieved high availability, IaC scaling, and automated provisioning. Future: S3 Remote State Backend with DynamoDB locking, multi-environment workspaces, CI/CD pipelines, CloudWatch monitoring.
- Visual: Grid showing Achievements vs. Roadmap.
```
