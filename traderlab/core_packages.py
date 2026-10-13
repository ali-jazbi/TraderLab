"""Operator membership review only; never owner confirmation or automatic grouping."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from .detection import instant
from .strategy import Bos, Zone, core_plan, direction, entry_reference

@dataclass(frozen=True)
class Package:
    id: str
    operator: str
    evidence: str
    approved: datetime
    fvg: str
    ob: str
    members: tuple[str, ...]

    @classmethod
    def read(cls, line):
        f=line.rstrip('\r\n').split('|')
        if len(f)!=8 or f[0]!='PACKAGE' or any(not x for x in f[1:]):
            raise ValueError('Malformed operator package')
        if not f[1].isascii() or not f[1].isalnum() or len(f[1])>12 or not f[4].isascii() or not f[4].isdigit():
            raise ValueError('Invalid package ID/UTC epoch')
        members=tuple(f[7].split(';'))
        if any(not x for x in members) or len(set(members))!=len(members) or int(f[4])<=0:
            raise ValueError('Invalid/duplicate BOS members')
        return cls(f[1],f[2],f[3],datetime.fromtimestamp(int(f[4]),timezone.utc),f[5],f[6],members)

def read_packages(path, symbol):
    with path.open(encoding='utf-8-sig') as f:
        if f.readline().rstrip('\r\n')!='CORE_OPERATOR_PACKAGES_V1|'+symbol:
            raise ValueError('Operator package symbol scope mismatch')
        rows=[Package.read(line) for line in f if line.strip()]
    if len({p.id for p in rows})!=len(rows):
        raise ValueError('Duplicate operator package IDs')
    members=[b for p in rows for b in p.members]
    if len(set(members))!=len(members):
        raise ValueError('BOS belongs to multiple operator packages')
    return rows

def resolve(package, bos, gaps, now):
    """Resolve only known detected records. Price/time fields cannot come from approval."""
    if now<=package.approved.replace(microsecond=999999):
        raise ValueError('Operator approval not yet available')
    gap=gaps.get(package.fvg)
    if not gap: raise ValueError('Operator FVG ID not observed')
    side=gap['side']; expected=package.fvg+(':C3' if side=='BUY' else ':C1')
    if package.ob!=expected: raise ValueError('OB is not the confirmed C3/C1 of this FVG')
    if gap['available_at']>package.approved: raise ValueError('Approval precedes confirmed FVG')
    if gap['fill_state']!='UNFILLED': raise ValueError('PARTIAL/FULL/unknown FVG not approved')
    zone=Zone.read(gap['zone'])
    if zone.high-zone.low<Decimal('2'): raise ValueError('FVG below20 strategy pips')
    candidates=[]
    for key in package.members:
        b=bos.get(key)
        if not b or b['side']!=side or b['qualified_at']>package.approved:
            raise ValueError('BOS not qualified at approval')
        if b.get('startup_history'): raise ValueError('Startup history not executable proof')
        level=Decimal(str(b['level']))
        if not zone.low<=level<=zone.high: raise ValueError('BOS wick outside FVG')
        candidates.append(Bos(key,entry_reference(side,level),Zone(level,level),level))
    plan=core_plan(side,candidates,{})
    if len({b.level for b in candidates})!=len(candidates): raise ValueError('Ambiguous equal BOS levels')
    for selected in plan.entries:
        returned=bos[selected.id].get('first_return_at')
        if returned and returned<=package.approved.replace(microsecond=999999):
            raise ValueError('First return consumed before operator approval')
    return {'mode':'OPERATOR_APPROVED_CORE','automatic_discovery':False,'package':package.id,
            'plan':plan,'execution_block':'TODO_STRATEGY_UNRESOLVED:single_be_anchor' if len(plan.entries)==1 else None}

def first_return_issue(candidate):
    """Actual native candidate evidence, not a synthetic replay signal."""
    if candidate.get('startup_history'): return 'STARTUP_HISTORY_NOT_EXECUTION_PROOF'
    if candidate.get('fill_state')!='UNFILLED': return 'PARTIAL_FULL_OR_UNKNOWN_FVG'
    if not candidate.get('first_return_consumed'): return 'NO_FIRST_DIRECTIONAL_RETURN'
    if not candidate.get('exact_quote'): return 'MISSED_EXACT_SIGNAL_QUOTE_NO_FILL'
    if not candidate.get('break_at'): return 'INTRABAR_BREAK_UNOBSERVED'
    if instant(candidate['first_return_at'])<instant(candidate['fvg_available_at']) or \
            'FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION' in candidate.get('reasons',[]):
        return 'FIRST_RETURN_BEFORE_CONFIRMED_AVAILABILITY'
    return None
