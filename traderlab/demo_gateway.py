"""Durable DEMO gateway reference model; injected transport is for tests only.

No MT5 connector is imported. Native production dispatch remains compile-time locked.
"""
import json
import sqlite3
from .broker import capability_issues, price_grid_compatible
from .strategy import number


class DemoLedger:
    def __init__(self, path, identity, enabled=False, reviewed=False):
        self.identity, self.enabled, self.reviewed = identity, enabled, reviewed
        self.db = sqlite3.connect(path, timeout=5)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        self.db.execute("CREATE TABLE IF NOT EXISTS intents (id TEXT PRIMARY KEY, opportunity TEXT UNIQUE, payload TEXT, state TEXT, evidence TEXT)")
        scope=json.dumps(identity,sort_keys=True)
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)',('identity',scope))
        if self.db.execute("SELECT value FROM meta WHERE key='identity'").fetchone()[0] != scope:
            self.db.close(); raise ValueError('LEDGER_ACCOUNT_SCOPE_MISMATCH')

    def close(self):
        self.db.close()

    def halt(self, reason):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)',('halt',reason))

    def preflight(self, snapshot, payload):
        if not self.enabled or not self.reviewed:
            raise ValueError('DEMO_GATEWAY_DISABLED_OR_UNREVIEWED')
        if snapshot['account_trade_mode'] != 'DEMO':
            raise ValueError('DEMO_ACCOUNT_REQUIRED')
        if any(snapshot[k] != v for k,v in self.identity.items()):
            raise ValueError('ACCOUNT_SCOPE_CHANGED')
        if not all(snapshot[k] is True for k in ('connected','trade_allowed','expert_allowed')):
            raise ValueError('TERMINAL_PERMISSION_UNAVAILABLE')
        if self.db.execute("SELECT value FROM meta WHERE key='halt'").fetchone() and payload['action'] == 'CORE':
            raise ValueError('PERSISTENT_EMERGENCY_STOP')
        if not snapshot.get('reconciled'):
            raise ValueError('BROKER_RECONCILIATION_REQUIRED')
        if payload['action'] not in ('CORE','CLOSE'):
            raise ValueError('UNSUPPORTED_OPERATION')
        if payload['action'] == 'CORE':
            if snapshot['margin_mode'] != 'HEDGING' or snapshot['currency'] != 'USD':
                raise ValueError('UNSUPPORTED_ACCOUNT_MODEL')
            if not all(payload['guards'].get(k) is True for k in ('strategy','first_touch','session','news','daily','quote')):
                raise ValueError('STRATEGY_GUARDS_NOT_APPROVED')
            if payload.get('fill_state') != 'UNFILLED' or payload.get('reverse') is not False:
                raise ValueError('UNSUPPORTED_PARTIAL_OR_REVERSE')
            if number(payload['volume']) != number('0.01'):
                raise ValueError('CANONICAL_LEG_REQUIRED')
            issues=capability_issues(snapshot['capabilities'],[payload['price'],payload['stop'],payload['target']],
                                     '0.02',snapshot['directional_volume'])
            if issues: raise ValueError(issues[0])
            if not snapshot.get('margin_check_passed') or not snapshot.get('order_check_passed'):
                raise ValueError('BROKER_CHECK_FAILED')
        if payload['action']=='CLOSE':
            position=next((p for p in snapshot.get('positions',[]) if p['ticket']==payload.get('position_id')),None)
            if position is None or position['symbol']!=payload.get('symbol') or number(position['volume'])!=number(payload.get('volume')):
                raise ValueError('AUTHORITATIVE_CLOSE_POSITION_REQUIRED')
        if not snapshot.get('exact_observed_quote') or not snapshot.get('order_check_passed'):
            raise ValueError('OBSERVED_QUOTE_AND_ORDER_CHECK_REQUIRED')

    def submit(self, intent_id, payload, snapshot, sender):
        """Intent committed BEFORE test transport. No automatic retries, even on reject."""
        self.preflight(snapshot,payload)
        serialized=json.dumps(payload,sort_keys=True,separators=(',',':'))
        try:
            self.db.execute('BEGIN IMMEDIATE')
            if payload['action']=='CORE' and self.db.execute("SELECT 1 FROM meta WHERE key='halt'").fetchone():
                raise ValueError('PERSISTENT_EMERGENCY_STOP')
            existing=self.db.execute('SELECT payload,state FROM intents WHERE id=?',(intent_id,)).fetchone()
            if existing:
                self.db.rollback()
                if existing[0] != serialized: raise ValueError('INTENT_PAYLOAD_CONFLICT')
                return existing[1]
            if self.db.execute("SELECT 1 FROM intents WHERE state IN ('INTENT','ACK','UNKNOWN')").fetchone():
                raise ValueError('UNRECONCILED_DISPATCH_EXISTS')
            self.db.execute('INSERT INTO intents VALUES (?,?,?,?,?)',
                            (intent_id,payload['opportunity'],serialized,'INTENT','{}'))
            self.db.commit()
        except Exception:
            self.db.rollback(); raise
        try:
            response=sender(payload)
            # A response never proves a fill. Rejections still consume the stable intent.
            state='REJECTED' if response.get('definitive_no_execution') is True else 'ACK'
            if response.get('partial'):
                self.halt('PARTIAL_FILL_REQUIRES_RECONCILIATION')
        except Exception:
            response={}; state='UNKNOWN'
        with self.db:
            self.db.execute('UPDATE intents SET state=?,evidence=? WHERE id=?',
                            (state,json.dumps(response,sort_keys=True),intent_id))
        return state

    def reconcile(self, snapshot, evidence):
        """Authoritative account history/positions, never infer rejection from absence."""
        if any(snapshot[k] != v for k,v in self.identity.items()) or snapshot.get('account_trade_mode') != 'DEMO':
            raise ValueError('RECONCILIATION_SCOPE_MISMATCH')
        if snapshot.get('history_complete') is not True:
            raise ValueError('BROKER_HISTORY_UNAVAILABLE')
        for item in evidence:
            if not item.get('source') or not item.get('deal_id'):
                raise ValueError('AUTHORITATIVE_DEAL_REQUIRED')
            with self.db:
                cursor=self.db.execute('UPDATE intents SET state=?,evidence=? WHERE id=?',
                    ('RECONCILED',json.dumps(item,sort_keys=True),item['intent_id']))
                if cursor.rowcount != 1: raise ValueError('UNKNOWN_BROKER_INTENT')
        return not self.db.execute("SELECT 1 FROM intents WHERE state IN ('INTENT','ACK','UNKNOWN')").fetchone()
