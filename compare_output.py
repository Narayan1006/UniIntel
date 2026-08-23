"""
Compare expected vs actual pipeline output field-by-field.
"""
import pandas as pd

exp = pd.read_csv('Unihack_ Expected Output - Delivery Format.csv', dtype=str).fillna('')
act = pd.read_csv('pipeline/output/enriched_output.csv', dtype=str).fillna('')

print('=' * 80)
print('SCHEMA COMPARISON')
print('=' * 80)
print(f'Expected: {len(exp)} rows, {len(exp.columns)} columns')
print(f'Actual:   {len(act)} rows, {len(act.columns)} columns')
print(f'All expected columns present in actual: {set(exp.columns).issubset(set(act.columns))}')
extra = set(act.columns) - set(exp.columns)
print(f'Extra columns in actual: {sorted(extra)}')
print()

# Compare each expected row
for idx in range(len(exp)):
    mpn = exp['Mfg_Part_Num'].iloc[idx]
    act_row = act[act['Mfg_Part_Num'] == mpn]
    if len(act_row) == 0:
        print(f'MPN {mpn} not found in actual output!')
        continue

    ar = act_row.iloc[0]
    er = exp.iloc[idx]

    print('=' * 80)
    print(f'MPN: {mpn}')
    print('=' * 80)

    fields = [
        ('BRAND_NAME', 'Brand Name'),
        ('MANUFACTURER_NAME', 'Manufacturer Name'),
        ('Classpath', 'Full Classpath'),
        ('Dept', 'Dept'),
        ('Class', 'Class'),
        ('Fine', 'Fine'),
        ('INVOICE_DESC', 'Invoice Desc (≤40 CAPS)'),
        ('SHORT_DESC', 'Short Desc'),
        ('LONG_DESC1', 'Long Desc 1'),
        ('MOBILE_DESC', 'Mobile Desc'),
        ('RETAIL_DESC', 'Retail Desc'),
        ('MARKETING_DESCRIPTION', 'Marketing Desc'),
        ('MFR URL', 'MFR Homepage URL'),
        ('Ref URL 1', 'Ref URL 1'),
        ('Ref URL 2', 'Ref URL 2'),
        ('Ref URL 3', 'Ref URL 3'),
        ('Ref URL 4', 'Ref URL 4'),
    ]

    for col, label in fields:
        if col not in exp.columns:
            continue
        ev = str(er[col])[:120]
        av = str(ar[col])[:120] if col in act.columns else 'MISSING'
        match = '[MATCH]' if ev.strip() == av.strip() else ('[DIFF]' if ev.strip() and av.strip() else '[MISS]')
        print(f'\n  [{match}] {label}')
        print(f'    Expected: {ev}')
        print(f'    Actual  : {av}')

print()
print('=' * 80)
print('FILL RATE SUMMARY (actual output, 999 rows)')
print('=' * 80)
key_cols = [
    'BRAND_NAME', 'Classpath', 'Dept', 'Class', 'Fine',
    'INVOICE_DESC', 'SHORT_DESC', 'LONG_DESC1', 'MOBILE_DESC',
    'RETAIL_DESC', 'MARKETING_DESCRIPTION',
    'MFR URL', 'Ref URL 1', 'Ref URL 2', 'Ref URL 3', 'Ref URL 4',
    'overall_trust_score'
]
for c in key_cols:
    if c in act.columns:
        filled = (act[c] != '').sum()
        pct = filled / len(act) * 100
        status = '[OK]' if pct >= 90 else ('[PARTIAL]' if pct >= 50 else '[EMPTY]')
        print(f'  {status} {c}: {filled}/{len(act)} ({pct:.0f}%)')

# Check attribute columns
print()
print('ATTRIBUTE COLUMN FILL CHECK (from expected structure):')
attr_cols = [c for c in exp.columns if 'Attribute' in c or 'ATTRIBUTE' in c or 'Value' in c]
print(f'  Attribute columns in expected: {len(attr_cols)}')
attr_in_act = [c for c in attr_cols if c in act.columns]
print(f'  Attribute columns in actual:   {len(attr_in_act)}')

# Check trust score
if 'overall_trust_score' in act.columns:
    scores = pd.to_numeric(act['overall_trust_score'], errors='coerce').dropna()
    print()
    print(f'TRUST SCORE STATS:')
    print(f'  Min: {scores.min():.1f}')
    print(f'  Max: {scores.max():.1f}')
    print(f'  Avg: {scores.mean():.1f}')
    print(f'  Rows ≥ 70: {(scores >= 70).sum()} ({(scores >= 70).mean()*100:.0f}%)')
    print(f'  Rows < 50 (review): {(scores < 50).sum()} ({(scores < 50).mean()*100:.0f}%)')
