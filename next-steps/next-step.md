# Phase 2 - Day-0 Bootstrap Hardening

The application is now functional and the infrastructure is operational.

The next goal is to make the repository fully reproducible for a clean:

terraform destroy
terraform apply

workflow.

Please implement the following improvements.

## Priority 1 - Secrets Manager Rebuild Safety

Current issue:

terraform destroy schedules the secret for deletion.

terraform apply fails because the secret name remains reserved during the AWS recovery window.

Required:

Review the current secret implementation and implement one of the following:

* unique secret naming strategy
* random suffix strategy
* alternative Terraform-safe solution

Goal:

terraform destroy
terraform apply

must succeed without waiting for AWS recovery windows.

---

## Priority 2 - Frontend Deployment Automation

Current issue:

Terraform provisions:

* frontend bucket
* CloudFront distribution

but does not deploy the React application.

Required:

Create:

deploy-frontend.sh

which automatically:

1. Reads Terraform outputs
2. Retrieves frontend bucket name
3. Retrieves CloudFront distribution ID
4. Creates frontend build
5. Uploads build artifacts
6. Performs CloudFront invalidation

Goal:

A new engineer should be able to run:

./deploy-frontend.sh

and obtain a working frontend deployment.

---

## Priority 3 - Documentation Alignment

Current issue:

DEPLOYMENT.md still documents:

Frontend EC2
Nginx

while Terraform deploys:

CloudFront
S3

Required:

Review:

docs/deployment/DEPLOYMENT.md

and update all frontend deployment instructions to match the actual architecture.

Remove references to:

* Frontend EC2
* Nginx frontend hosting

Document:

CloudFront + S3 deployment flow.

---

## Priority 4 - S3 Rebuild Safety

Review both buckets:

* frontend bucket
* documents bucket

Determine whether:

force_destroy = true

should be enabled.

If appropriate, implement it and document implications.

---

## Priority 5 - Day-0 Validation

After implementation perform a final audit.

Answer:

Can a new engineer:

1. Clone repository
2. Configure terraform.tfvars
3. Run terraform apply
4. Run deploy-frontend.sh

and obtain a fully working deployment?

Provide any remaining blockers.
