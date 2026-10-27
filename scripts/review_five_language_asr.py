"""Zero-inference manual-review material from the frozen five-language run."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.offline_russian_capture_ab import create_output,write,offline_guard
from scripts.review_ru_continuous_baseline import human_review_items

NEGATION={
    'zh':r'不要|不能|没有|不是|别|不|没|未|无',
    'en':r"\bnot\b|\bno\b|\bnever\b|\bwithout\b|n't\b",
    'ja':r'なかった|ません|ない|禁止|なく',
    'ko':r'지\s*마|않|못|없|아니|\b안\b',
    'ru':r'\b(?:не|нет|ни|нельзя|никогда|без)\b',
}


def cues(language,reference,hypothesis):
    def normalize(t):return unicodedata.normalize('NFKC',t).casefold().replace('’',"'")
    reference,hypothesis=normalize(reference),normalize(hypothesis)
    neg=lambda t:re.findall(NEGATION[language],t)
    digits=lambda t:re.findall(r'\d+(?:[.,]\d+)*',t)
    return dict(reference_negation_cues=neg(reference),hypothesis_negation_cues=neg(hypothesis),
        negation_cue_difference=Counter(neg(reference))!=Counter(neg(hypothesis)),
        reference_digits=digits(reference),hypothesis_digits=digits(hypothesis),digit_surface_difference=digits(reference)!=digits(hypothesis),
        human_semantic_accuracy=None,entity_retention=None,tail_complete=None,
        status='suspicions only; morphology, homophones, spoken numbers and publisher errors may produce false flags')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    with offline_guard():
        plan=json.loads((args.results/'plan.json').read_text('utf-8'));status=json.loads((args.results/'status.json').read_text('utf-8'))
        if status['status']!='complete':raise ValueError('No complete baseline; do not fabricate final results')
        if hashlib.sha256(args.manifest.read_bytes()).hexdigest()!=plan['manifest_sha256']:raise ValueError('Frozen manifest changed')
        manifest=json.loads(args.manifest.read_text('utf-8'));lookup={r['id']:r for r in manifest['records']}
        if any(args.output.resolve().is_relative_to(x.resolve()) for x in [args.results,args.manifest.parent,ROOT/'voxgo']):raise ValueError('Protect original evidence/runtime')
        output=create_output(args.output);items={};recordings=[]
        for spec in plan['schedule']:
            record=lookup[spec['record_id']];run=args.results/spec['id'];r=json.loads((run/'result.json').read_text('utf-8'));a=json.loads((run/'assessment.json').read_text('utf-8'))
            if record['split']=='dev':
                recordings.append(dict(id=record['id'],language=record['language'],strategy=spec['strategy'],reference=record['reference_text'],raw=a['raw'],retained=a['retained'],translation_input=a['translation_input'],
                    cues=cues(record['language'],record['reference_text'],a['translation_input']),reference_status=record['reference_status'],human_review='pending'))
            for item in human_review_items(r,record,run):
                item['source_language']=spec['source_language']
                for o in item['observations']:o['source_language']=spec['source_language']
                if item['id'] in items:items[item['id']]['observations']+=item['observations']
                else:items[item['id']]=item
        write(output/'human-segment-review.json',list(items.values()));write(output/'recording-review.json',recordings)
        write(output/'provenance.json',dict(no_inference=True,manual_labels_all_pending=True,api_requests=0,manifest_sha256=plan['manifest_sha256'],
            code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),raw_plan_sha256=hashlib.sha256((args.results/'plan.json').read_bytes()).hexdigest()))
        print(json.dumps(dict(segment_review_items=len(items),recording_review_rows=len(recordings),api_requests=0)))


if __name__=='__main__':main()
