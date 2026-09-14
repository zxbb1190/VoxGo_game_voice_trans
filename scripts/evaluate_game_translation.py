"""Compare authored scenarios; outputs require human semantic review, not pass counts."""
import json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ctranslate2,sentencepiece
from voxgo.translation.local_models import model_path
from voxgo.translation.glossary import preprocess,postprocess
root=model_path()
engines={}
def translate(text,src,dst,tag=True):
 d=src+'-'+dst
 if d not in engines:
  p=root/d
  engines[d]=(ctranslate2.Translator(str(p),device='cpu',compute_type='int8',inter_threads=1,intra_threads=2),sentencepiece.SentencePieceProcessor(model_file=str(p/'source.spm')),sentencepiece.SentencePieceProcessor(model_file=str(p/'target.spm')))
 model,source,target=engines[d]
 tokens=source.encode(text,out_type=str)
 if tag and d=='en-zh':tokens.insert(0,'>>cmn_Hans<<')
 return target.decode(model.translate_batch([tokens+['</s>']],beam_size=2,max_input_length=256,max_decoding_length=256)[0].hypotheses[0])
def main():
 data=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
 cases=data['cases'] if isinstance(data,dict) else data
 rows=[]
 for c in cases:
  src=c['source_lang'];dst=c['target_lang'];text=c['text']
  baseline=translate(text,src,dst,False);tagged=translate(text,src,dst)
  plan=preprocess(text,src,dst)
  enhanced=plan.translated_override or postprocess(translate(plan.normalized_text,src,dst),plan)
  rows.append(dict(c,baseline=baseline,tagged=tagged,enhanced=enhanced,matched=bool(plan.corrections or plan.translated_override),normalized=plan.normalized_text))
 Path(sys.argv[2]).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 print('evaluated',len(rows),flush=True)
if __name__=='__main__':main()
