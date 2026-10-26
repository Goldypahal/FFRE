# Owner Manual Steps Required

This document details required operational or out-of-repo actions that cannot or should not be performed autonomously by the agent (e.g. key rotation, public repository setting changes, history rewriting).

---

## High Priority Actions for Repository Owner
1. **Rotate All Previously Committed Secrets**:
   - `SECRET_KEY`, `REFRESH_SECRET_KEY`, and database passwords previously committed to `.env`, `docker-compose.yml`, or `k8s/secrets.yaml` must be treated as permanently compromised.
   - Generate new cryptographic tokens (minimum 256-bit entropy) for production and store in a secure secret manager (e.g. AWS Secrets Manager, HashiCorp Vault).
2. **Purge Historical Vault Files & Secrets from Git History**:
   - Run `git filter-repo` or BFG Repo-Cleaner on the remote repository to purge `backend/data/vault/` and historical secret commits prior to publishing or open-sourcing.
3. **Repository Visibility & Access Control**:
   - Ensure repository visibility is set to Private until all sensitive history is purged.
