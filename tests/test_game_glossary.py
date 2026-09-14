import unittest
from voxgo.translation.glossary import preprocess, postprocess
class GlossaryTests(unittest.TestCase):
 def test_reload_cover_composition(self):
  p=preprocess('我换子弹你帮我架一下','zh','en'); self.assertEqual(p.translated_override,"I'm reloading. Cover me.")
 def test_exact_commands(self):
  self.assertEqual(preprocess('enemy spotted','en','zh').translated_override,'发现敌人')
  self.assertEqual(preprocess('撤退','zh','en').translated_override,'Fall back')
 def test_ordinary_prose_is_untouched(self):
  for text in ['Please hold this item for me','He is one shot away from death','有人在门口吗？','救我的猫']:
   p=preprocess(text,'en' if text[0].isascii() else 'zh','zh' if text[0].isascii() else 'en'); self.assertEqual(p.normalized_text,text); self.assertEqual(p.translated_override,'')
 def test_negation_and_pronouns_not_rewritten(self):
  for text in ['不要撤退','我不需要治疗','不是敌人','I do not need healing','Do not push now']:
   source='zh' if not text[0].isascii() else 'en'; target='en' if source=='zh' else 'zh'; self.assertFalse(preprocess(text,source,target).translated_override)
 def test_punctuation_spacing(self):
  self.assertEqual(preprocess('  PUSH! ','en','zh').translated_override,'压上')
 def test_other_languages_passthrough(self): self.assertEqual(preprocess('enemy','fr','zh').normalized_text,'enemy')
 def test_postprocess(self):
  p=preprocess('go','en','zh'); self.assertEqual(postprocess('wrong',p),'走'); self.assertEqual(postprocess('free',preprocess('unknown','en','zh')),'free')
 def test_compound_commands_without_punctuation(self):
  self.assertEqual(preprocess('敌人在我们后面撤退','zh','en').translated_override, 'Enemies behind us. Fall back.')
  self.assertEqual(preprocess('我正在换子弹你帮我架一下','zh','en').translated_override, "I'm reloading. Cover me.")
  self.assertEqual(preprocess('找掩体我在补甲','zh','en').translated_override, "Find cover. I'm repairing my armor.")
 def test_embedded_context_normalization(self):
  p=preprocess('我正在换子弹，请帮我看一下桥对面','zh','en')
  self.assertEqual(p.normalized_text,'我正在重新装填弹药，请帮我看一下桥对面')
  self.assertEqual(postprocess('I am changing bullets, please watch the bridge.',p),'I am reloading, please watch the bridge.')
  self.assertEqual(postprocess('He is changing bullets.',p),'He is changing bullets.')
  self.assertEqual(postprocess('I am not changing bullets.',p),'I am not changing bullets.')
 def test_context_negatives(self):
  for text in ['我正在换子弹，你不知道吗？','敌人在我们后面的故事很好看','有人','架一下照片','救我','没有敌人倒地了']:
   p=preprocess(text,'zh','en'); self.assertEqual(p.normalized_text,text);self.assertFalse(p.translated_override)
  for text in ['hold','one shot','knocked','drop','rotate','I knocked on the door']:
   self.assertFalse(preprocess(text,'en','zh').translated_override)
 def test_guarded_extended_terms(self):
  for text in ['帮我拉枪线','开枪时压枪','先别舔包','我倒地了扶我','补掉倒地的敌人','附近有敌人的脚步声','我正在装弹','我残血了']:
   self.assertTrue(preprocess(text,'zh','en').translated_override,text)
  for text in ['扶我奶奶起来','有人来救我吗','我倒地了？','“换子弹”是什么意思','脚步','补掉']:
   p=preprocess(text,'zh','en'); self.assertEqual(p.normalized_text,text); self.assertFalse(p.translated_override)
  self.assertFalse(preprocess('reload?','en','zh').translated_override)
 def test_embedded_negation_is_preserved(self):
  for original,expected in [('我没换子弹','我没重新装填弹药'),('别换子弹','别重新装填弹药'),('他不是残血，别冲','他生命值并不低，别冲'),('先别舔包，等我','先别搜刮战利品，等我')]:
   plan=preprocess(original,'zh','en')
   self.assertEqual(plan.normalized_text,expected)
   self.assertFalse(plan.translated_override)
 def test_ordinary_english_homonyms_are_not_normalized(self):
  for text in ['Reload the page','Please cover the soup','Hold the door open','I need to finish my homework','We filmed it in one shot']:
   plan=preprocess(text,'en','zh')
   self.assertEqual(plan.normalized_text,text)
   self.assertFalse(plan.translated_override)
 def test_source_gates_post_corrections(self):
  p=preprocess('先别舔包，等我','zh','en')
  self.assertEqual(postprocess("Don't scratch the booty.",p),"Don't loot.")
  plain=preprocess('普通句子','zh','en')
  self.assertEqual(postprocess('scratch the booty',plain),'scratch the booty')
  health=preprocess('I am low on health.','en','zh')
  self.assertEqual(postprocess('我身体不好',health),'我血量很低')
  mixed=preprocess('I am low on health, but my mother is in poor health.','en','zh')
  self.assertEqual(postprocess('我身体不好，但我妈妈身体不好',mixed),'我血量很低，但我妈妈身体不好')
  reversed_plan=preprocess('My mother is in poor health, and I am low on health.','en','zh')
  self.assertEqual(postprocess('我妈妈身体不好，我身体不好',reversed_plan),'我妈妈身体不好，我身体不好')
 def test_catalog_size(self):
  from voxgo.translation.glossary import glossary_terms
  self.assertGreaterEqual(len(glossary_terms('zh','en')),60)
  self.assertGreaterEqual(len(glossary_terms('en','zh')),60)
if __name__=='__main__': unittest.main()
