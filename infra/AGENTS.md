# infra/ — Terraform (nested)
- Code only: agents never run terraform plan/apply against any account and never hold AWS credentials; dev/stage are applied by the CI deploy role after a human merge; prod by the named human after the gates.
- Regions ap-south-1 (primary) and ap-south-2 (DR) only, plus the documented global / us-east-1 CloudFront exceptions; WRITES_* flags false in every task definition.
## Code Review Rules
- P0: an aws_iam_access_key, a long-lived credential, a prod trust path reachable from a PR or main job, a write flag defaulting to true.
- P1: a resource outside the allowed regions, compliance-mode Object Lock on a prefix that may hold PII.
