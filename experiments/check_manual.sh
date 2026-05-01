python -c "
import json
with open('experiments/eval_results.json') as f:
    results = json.load(f)
for q in ['Q01', 'Q06', 'Q14', 'Q15', 'Q24']:
    r = next((x for x in results if x['query_id']==q and x['variant']=='few_shot'), None)
    if r:
        print(f'=== {q} (few_shot) ===')
        print(f'Question: {r[\"question\"]}')
        print(f'')
        print(f'Response:')
        print(r['response_text'])
        print(f'')
        print(f'Cited PMIDs: {r[\"cited_pmids\"]}')
        print()
        print('-'*70)
        print()
" > experiments/spot_check_responses.txt