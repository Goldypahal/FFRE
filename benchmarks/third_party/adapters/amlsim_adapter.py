"""
IBM AMLSim Adapter for FFIRE Ingestion and Evaluation.

Ingests IBM AMLSim synthetic transaction networks, maps attributes into FFIRE schema,
quarantines malformed rows, and isolates ground-truth typology labels to prevent leakage.
"""

import os
import csv
import json
import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Tuple, Optional

import sys
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import models


class AMLSimAdapter:
    """
    Adapter converting IBM AMLSim datasets into FFIRE relational models
    and generating zero-leakage evaluation cases with gold-standard labels.
    """

    def __init__(
        self,
        tenant_id: str = "amlsim_eval_tenant",
        base_dir: Optional[str] = None,
        base_timestamp: Optional[datetime.datetime] = None,
    ):
        self.tenant_id = tenant_id
        if base_dir is None:
            self.base_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "datasets")
            )
        else:
            self.base_dir = base_dir

        self.base_timestamp = base_timestamp or datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.alerts: Dict[str, Dict[str, Any]] = {}
        self.valid_transactions: List[Dict[str, Any]] = []
        self.quarantined_records: List[Dict[str, Any]] = []
        self.gold_records: Dict[str, Dict[str, Any]] = {}

    def load_accounts(self, accounts_filename: str = "amlsim_accounts.csv") -> Dict[str, Dict[str, Any]]:
        """Parse AMLSim accounts file and populate memory index."""
        path = os.path.join(self.base_dir, accounts_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"AMLSim accounts file not found: {path}")

        accounts_map = {}
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                acct_id = row["ACCOUNT_ID"].strip()
                try:
                    init_bal = Decimal(str(row.get("INIT_BALANCE", "0.00")).strip())
                except InvalidOperation:
                    init_bal = Decimal("0.00")

                accounts_map[acct_id] = {
                    "account_id": acct_id,
                    "customer_id": row.get("CUSTOMER_ID", f"CUST_{acct_id}").strip(),
                    "initial_balance": init_bal,
                    "model_type": row.get("MODEL_TYPE", "normal").strip(),
                    "is_sar": row.get("IS_SAR", "0").strip() == "1",
                }

        self.accounts = accounts_map
        return self.accounts

    def load_alerts(self, alerts_filename: str = "amlsim_alerts.json") -> Dict[str, Dict[str, Any]]:
        """Parse AMLSim alerts ground-truth definitions."""
        path = os.path.join(self.base_dir, alerts_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"AMLSim alerts file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            alerts_data = json.load(f)

        alerts_map = {}
        for alert in alerts_data:
            alert_id = alert["alert_id"]
            alerts_map[alert_id] = alert

        self.alerts = alerts_map
        return self.alerts

    def load_transactions(
        self, transactions_filename: str = "amlsim_transactions.csv"
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parse and validate AMLSim transactions.
        Splits output into valid ingestion records and quarantined records.
        Constructs external gold records with ground-truth typology labels.
        """
        if not self.accounts:
            self.load_accounts()
        if not self.alerts:
            self.load_alerts()

        path = os.path.join(self.base_dir, transactions_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"AMLSim transactions file not found: {path}")

        valid_txns = []
        quarantined = []
        gold_map = {}

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=1):
                raw_amount = row.get("amount", "").strip()
                orig_acc = row.get("nameOrig", "").strip()
                dest_acc = row.get("nameDest", "").strip()
                raw_step = row.get("step", "").strip()
                txn_type = row.get("type", "").strip().upper()
                is_sar_raw = row.get("isSAR", "").strip()
                alert_id = row.get("alert_id", "").strip()

                # Validation 1: Amount must be valid positive Decimal
                try:
                    amount = Decimal(raw_amount)
                    if amount <= 0:
                        quarantined.append({
                            "row_index": idx,
                            "raw_record": row,
                            "reason": f"Non-positive transaction amount: {raw_amount}"
                        })
                        continue
                except (InvalidOperation, TypeError):
                    quarantined.append({
                        "row_index": idx,
                        "raw_record": row,
                        "reason": f"Malformed or non-numeric amount: {raw_amount}"
                    })
                    continue

                # Validation 2: Source account must exist
                if orig_acc not in self.accounts:
                    quarantined.append({
                        "row_index": idx,
                        "raw_record": row,
                        "reason": f"Originator account '{orig_acc}' does not exist in accounts master"
                    })
                    continue

                # Validation 3: Step must be positive integer
                try:
                    step_int = int(raw_step)
                    if step_int < 0:
                        raise ValueError()
                except ValueError:
                    quarantined.append({
                        "row_index": idx,
                        "raw_record": row,
                        "reason": f"Invalid step timestamp: {raw_step}"
                    })
                    continue

                txn_id = f"TXN_AML_{step_int}_{idx:04d}"
                # Explicit timezone handling (UTC)
                explicit_ts = self.base_timestamp + datetime.timedelta(hours=step_int)

                # Channel derivation from AMLSim type
                channel = "wire" if txn_type == "TRANSFER" else "pos" if txn_type == "PAYMENT" else "web"

                # 1. Feature Record for FFIRE Ingestion (Zero Label Leakage)
                # IMPORTANT: isSAR, alert_id, and typology are strictly excluded!
                feature_record = {
                    "txn_id": txn_id,
                    "account_id": orig_acc,
                    "counterparty": dest_acc,
                    "amount": amount,
                    "currency": "USD",
                    "timestamp": explicit_ts,
                    "channel": channel,
                    "status": "COMPLETED",
                    "tenant_id": self.tenant_id,
                }
                valid_txns.append(feature_record)

                # 2. Ground-Truth Gold Record (Kept separate from engine evidence)
                is_sar = is_sar_raw == "1"
                alert_info = self.alerts.get(alert_id, {})
                typology = alert_info.get("model_type", "none") if is_sar else "none"

                gold_map[txn_id] = {
                    "case_id": f"CASE_{txn_id}",
                    "txn_id": txn_id,
                    "step": step_int,
                    "is_sar": is_sar,
                    "alert_id": alert_id if is_sar else None,
                    "typology": typology,
                    "amount": float(amount),
                    "source_account": orig_acc,
                    "dest_account": dest_acc,
                    "reason": alert_info.get("reason", "Standard commercial activity" if not is_sar else "Suspicious flow"),
                }

        self.valid_transactions = valid_txns
        self.quarantined_records = quarantined
        self.gold_records = gold_map

        return valid_txns, quarantined

    def seed_to_database(self, db_session) -> Dict[str, int]:
        """
        Seed parsed accounts, customers, and valid transactions into FFIRE database.
        Strictly enforces tenant isolation and zero label leakage.
        """
        if not self.valid_transactions:
            self.load_transactions()

        # 1. Seed unique customers
        cust_created = 0
        acct_created = 0
        txn_created = 0

        existing_custs = {c[0] for c in db_session.query(models.Customer.customer_id).all()}
        existing_accts = {a[0] for a in db_session.query(models.Account.account_id).all()}
        existing_txns = {t[0] for t in db_session.query(models.Transaction.txn_id).all()}

        # Seed default merchant for AMLSim commercial payments
        merch_id = f"MERCH_AMLSIM_{self.tenant_id}"
        existing_merch = db_session.query(models.Merchant).filter_by(merchant_id=merch_id, tenant_id=self.tenant_id).first()
        if not existing_merch:
            merch = models.Merchant(
                merchant_id=merch_id,
                tenant_id=self.tenant_id,
                name="AMLSim Commercial Network",
                category="COMMERCIAL_SERVICES",
                risk_score=Decimal("0.100")
            )
            db_session.add(merch)
            db_session.commit()

        for acct_data in self.accounts.values():
            cust_id = acct_data["customer_id"]
            if cust_id not in existing_custs:
                cust = models.Customer(
                    customer_id=cust_id,
                    tenant_id=self.tenant_id,
                    kyc_status="VERIFIED",
                    risk_tier="MEDIUM"
                )
                cust.name = f"Entity {cust_id}"
                cust.email = f"{cust_id.lower()}@amlsim-network.org"
                db_session.add(cust)
                existing_custs.add(cust_id)
                cust_created += 1

            acct_id = acct_data["account_id"]
            if acct_id not in existing_accts:
                acct = models.Account(
                    account_id=acct_id,
                    tenant_id=self.tenant_id,
                    customer_id=cust_id,
                    account_type="BUSINESS" if "CORP" in acct_id or "SRC" in acct_id else "CHECKING",
                    balance=acct_data["initial_balance"]
                )
                db_session.add(acct)
                existing_accts.add(acct_id)
                acct_created += 1

        db_session.commit()

        # Seed valid transactions (zero SAR / typology columns)
        for t_dict in self.valid_transactions:
            t_id = t_dict["txn_id"]
            if t_id not in existing_txns:
                txn = models.Transaction(
                    txn_id=t_id,
                    tenant_id=self.tenant_id,
                    account_id=t_dict["account_id"],
                    merchant_id=merch_id,
                    amount=t_dict["amount"],
                    currency=t_dict["currency"],
                    status=t_dict["status"],
                    timestamp=t_dict["timestamp"],
                    channel=t_dict["channel"],
                    counterparty=t_dict["counterparty"],
                )
                db_session.add(txn)
                existing_txns.add(t_id)
                txn_created += 1

        db_session.commit()

        return {
            "customers": cust_created,
            "accounts": acct_created,
            "transactions": txn_created,
            "quarantined": len(self.quarantined_records)
        }

    def build_evaluation_cases(self) -> List[Dict[str, Any]]:
        """
        Build standardized evaluation cases conforming to case.schema.json.
        Returns cases categorized into suspicious_typology, benign_control,
        and insufficient_evidence.
        """
        if not self.gold_records:
            self.load_transactions()

        cases = []
        for txn_id, gold in self.gold_records.items():
            is_sar = gold["is_sar"]
            typology = gold["typology"]

            category = "suspicious_typology" if is_sar else "benign_control"
            ground_truth_label = "SUSPICIOUS" if is_sar else "BENIGN"

            # Identify related transactions in the same alert pattern if suspicious
            related_txns = []
            related_accs = [gold["source_account"], gold["dest_account"]]
            alert_id = gold["alert_id"]

            if alert_id:
                for other_id, other_gold in self.gold_records.items():
                    if other_id != txn_id and other_gold.get("alert_id") == alert_id:
                        related_txns.append(other_id)
                        if other_gold["source_account"] not in related_accs:
                            related_accs.append(other_gold["source_account"])
                        if other_gold["dest_account"] not in related_accs:
                            related_accs.append(other_gold["dest_account"])

            cluster_id = f"sar_{alert_id}" if is_sar and alert_id else f"benign_{gold['source_account']}"

            case_obj = {
                "case_id": gold["case_id"],
                "dataset": "ibm_amlsim_v1",
                "scenario_id": alert_id or "scenario_benign_baseline",
                "cluster_id": cluster_id,
                "category": category,
                "typology": typology if typology != "none" else None,
                "target_transaction_id": txn_id,
                "related_transaction_ids": related_txns,
                "related_account_ids": related_accs,
                "ground_truth_label": ground_truth_label,
                "ground_truth_edges": [
                    {
                        "source": gold["source_account"],
                        "dest": gold["dest_account"],
                        "amount": gold["amount"],
                        "step": gold["step"],
                        "is_sar": is_sar
                    }
                ],
                "expected_evidence_ids": [
                    f"txn_{txn_id}",
                    f"account_{gold['source_account']}",
                    f"customer_{self.accounts.get(gold['source_account'], {}).get('customer_id', '')}"
                ],
                "expected_abstention": False,
                "user_query": f"Investigate transaction {txn_id} involving account {gold['source_account']} and {gold['dest_account']}.",
                "reference_answer": gold["reason"],
                "metadata": {
                    "alert_id": alert_id,
                    "cluster_id": cluster_id,
                    "step": gold["step"],
                    "amount": gold["amount"],
                    "tenant_id": self.tenant_id
                }
            }
            cases.append(case_obj)

        # Add 2 intentional insufficient-evidence cases (testing abstention)
        cases.append({
            "case_id": "CASE_INSUFFICIENT_01",
            "dataset": "ibm_amlsim_v1",
            "scenario_id": "scenario_insufficient_evidence",
            "cluster_id": "cluster_insufficient_evidence",
            "category": "insufficient_evidence",
            "typology": None,
            "target_transaction_id": "TXN_DISCONNECTED_01",
            "related_transaction_ids": [],
            "related_account_ids": ["ACC_DISC_01"],
            "ground_truth_label": "INSUFFICIENT_EVIDENCE",
            "ground_truth_edges": [],
            "expected_evidence_ids": [],
            "expected_abstention": True,
            "user_query": "Investigate disconnected transaction TXN_DISCONNECTED_01.",
            "reference_answer": "Insufficient evidence available to reach a conclusive finding; must escalate.",
            "metadata": {"tenant_id": self.tenant_id, "cluster_id": "cluster_insufficient_evidence"}
        })

        return cases

    def load_hardened_challenge_cases(self, challenge_filename: str = "amlsim_hardened_challenge.json") -> List[Dict[str, Any]]:
        """
        Load the 16-case Development Challenge evaluation battery.
        Contains benign high-value corporate/escrow transactions, suspicious low-value micro-structuring,
        near-miss non-illicit graph patterns (refunds, supply chains), and mixed-activity networks.
        Used for development diagnostic audits and tuning.
        """
        path = os.path.join(self.base_dir, challenge_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Challenge dataset not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        # Inject tenant_id dynamically into cases and metadata
        for c in cases:
            if "metadata" not in c:
                c["metadata"] = {}
            c["metadata"]["tenant_id"] = self.tenant_id

        return cases

    def load_held_out_test_cases(self, test_filename: str = "amlsim_held_out_test.json") -> List[Dict[str, Any]]:
        """
        Load the untouched 24-case Held-Out Test evaluation battery.
        Guaranteed untouched during development, rule calibration, and prompt engineering.
        Contains balanced, non-separable scenarios across benign high-value wires, micro-structuring,
        near-miss non-illicit graph topologies, multi-hop circular flows, and fail-closed abstentions.
        """
        path = os.path.join(self.base_dir, test_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Held-out test dataset not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        for c in cases:
            if "metadata" not in c:
                c["metadata"] = {}
            c["metadata"]["tenant_id"] = self.tenant_id

        return cases

