# Secrets Audit & Management Protocol

**Audit Date:** November 2026  
**Auditor:** FFIRE Security & Benchmark Integrity Team  
**Scope:** `k8s/secrets.yaml`, `.env*`, `backend/.env*`, and Git version history.

---

## 1. Executive Summary

As part of the FFIRE-Bench credibility and operational security reset (Credibility Blocker B6), an exhaustive secrets audit was performed across all configuration files, Kubernetes manifests, and environment templates.

**Audit Verdict:** **PASS (Clean)**. No live production credentials, API keys, or cryptographic private keys are committed in repository plain-text. All files utilize explicit placeholder formats (`REPLACE_WITH_...` or `your_openai_api_key_here`).

---

## 2. Inventory of Audited Files

| Path | Finding | Status | Action Required |
|---|---|---|---|
| `k8s/secrets.yaml` | Contains `stringData` with environment variable substitution syntax (`${DATABASE_URL:-postgresql://ffre_user:REPLACE_WITH_SECURE_POSTGRES_PASSWORD...}`) | Clean | Ensure Kubernetes deployments populate secrets via SealedSecrets, HashiCorp Vault, or CI/CD `envsubst`. |
| `.env.example` | Standard template with sanitized placeholder keys | Clean | Safe to commit. |
| `backend/.env` | Single placeholder: `OPENAI_API_KEY=your_openai_api_key_here` | Clean | Added to `.gitignore` to prevent developer keys from accidental commits. |
| `backend/.env.example` | Sanitized service URLs and mock credentials | Clean | Safe to commit. |
| `backend/.env.production.example` | Sanitized production template with instructions | Clean | Safe to commit. |

---

## 3. Secret Rotation & Key Isolation Rules

1. **Production Deployment**:
   - Production secrets MUST never be stored in plain Kubernetes Secret YAMLs.
   - Use Kubernetes External Secrets Operator (ESO) connected to AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault.
2. **Attestation Keys (Ed25519)**:
   - FFIRE-Bench results and attestation bundles are digitally signed using Ed25519 private keys.
   - Benchmark private signing keys must reside in hardware security modules (HSM) or KMS with strict IAM audit logging; only public keys are distributed in `data/keys/`.
3. **Canary String Confidentiality**:
   - Private test split files carry unique canary GUIDs (`FFIRE-BENCH-CANARY-<guid>`).
   - Private test cases and canary strings must never be uploaded to public repositories, public web pages, or shared with external evaluators prior to official scoring service submission.

---

## 4. Gitignore Rule Enforcement

The `.gitignore` has been hardened to ensure all local environment files across subdirectories are ignored:
```gitignore
# Environment files across all subdirectories
**/.env
**/.env.*
!**/.env.example
!**/.env.production.example
```
