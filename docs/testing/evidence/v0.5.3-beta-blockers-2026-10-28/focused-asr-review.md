# Focused ASR review (saved evidence only)

Human transcription, word/frame alignment and semantic review: pending.

## beta-zh-1953-10144930991730701959 / formal

Reference (publisher, pending): 他随后被转送到剑桥的阿登布鲁克医院。
Raw: 它隨後被傳轉送到劍橋的阿登 不如可以呀
Translation input: 它隨後被傳轉送到劍橋的阿登

Counts: `{"captured": 3, "work_items": 3, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 1, "post_asr_drops": 1, "translation_ready": 1, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 1, "budget_pre_asr_drops": 0, "forced_capture_cuts": 1}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(0, 7680)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-8.2dB)
- s002: [(7680, 55680)]; raw={'text': '它隨後被傳轉送到劍橋的阿登', 'language': 'zh', 'language_probability': 1.0, 'avg_logprob': -0.32393814535701976, 'no_speech_prob': 0.0038633598014712334, 'compression_ratio': 0.78, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': '它隨後被傳轉送到劍橋的阿登', 'runaway_guarded': False}; rejection=
- s003: [(55680, 76800)]; raw={'text': '不如可以呀', 'language': 'zh', 'language_probability': 1.0, 'avg_logprob': -1.2158960274287633, 'no_speech_prob': 0.24448327720165253, 'compression_ratio': 0.625, 'segment_count': 1, 'duration_seconds': 1.32, 'raw_text': '不如可以呀', 'runaway_guarded': False}; rejection=global_asr_low_logprob_short avg_logprob=-1.22

## beta-zh-1830-10147383166642115307 / formal

Reference (publisher, pending): 执政党西南非洲人民组织 (SWAPO) 也在议会选举中保持了多数席位。
Raw: 執政黨西南非洲人民組織也在議會上 現在就中保速了多數席位
Translation input: 執政黨西南非洲人民組織也在議會上 現在就中保速了多數席位

Counts: `{"captured": 3, "work_items": 3, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 1, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 0, "forced_capture_cuts": 1}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(0, 7680)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-17.0dB)
- s002: [(7680, 55680)]; raw={'text': '執政黨西南非洲人民組織也在議會上', 'language': 'zh', 'language_probability': 1.0, 'avg_logprob': -0.27910764664411547, 'no_speech_prob': 0.026513170450925827, 'compression_ratio': 0.8135593220338984, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': '執政黨西南非洲人民組織也在議會上', 'runaway_guarded': False}; rejection=
- s003: [(55680, 94080)]; raw={'text': '現在就中保速了多數席位', 'language': 'zh', 'language_probability': 1.0, 'avg_logprob': -0.8246371362890516, 'no_speech_prob': 0.03610260784626007, 'compression_ratio': 0.75, 'segment_count': 1, 'duration_seconds': 2.4, 'raw_text': '現在就中保速了多數席位', 'runaway_guarded': False}; rejection=

## beta-zh-1905-10279011772105822622 / formal

Reference (publisher, pending): 摩尔多瓦的首都是基希讷乌。当地语言是罗马尼亚语，但俄语也被广泛使用。
Raw: 摩爾多瓦的首都是新金納物當地的 是羅馬年阿宇,但鵝魚也被廣泛使用
Translation input: 摩爾多瓦的首都是新金納物當地的

Counts: `{"captured": 3, "work_items": 3, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 1, "post_asr_drops": 1, "translation_ready": 1, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 1, "budget_pre_asr_drops": 1, "forced_capture_cuts": 2}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(7680, 57600)]; raw={'text': '摩爾多瓦的首都是新金納物當地的', 'language': 'zh', 'language_probability': 1.0, 'avg_logprob': -0.5062272223559293, 'no_speech_prob': 0.10091536492109299, 'compression_ratio': 0.8035714285714286, 'segment_count': 1, 'duration_seconds': 3.12, 'raw_text': '摩爾多瓦的首都是新金納物當地的', 'runaway_guarded': False}; rejection=
- s002: [(57600, 105600)]; raw={'text': '是羅馬年阿宇,但鵝魚也被廣泛使用', 'language': 'zh', 'language_probability': 1.0, 'avg_logprob': -0.5399216587344805, 'no_speech_prob': 0.6729507446289062, 'compression_ratio': 0.8070175438596491, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': '是羅馬年阿宇,但鵝魚也被廣泛使用', 'runaway_guarded': False}; rejection=global_asr_no_speech_short no_speech=0.67
- s003: [(105600, 113280)]; raw=None; rejection=asr_budget_weak_drop

## beta-en-1972-10233995782544396174 / formal

Reference (publisher, pending): Many people don't think about them as dinosaurs because they have feathers and can fly.
Raw: 
Translation input: (empty)

Counts: `{"captured": 3, "work_items": 3, "merges": 0, "asr_attempted": 0, "asr_completed": 0, "asr_missing_completion": 0, "pre_asr_drops": 3, "post_asr_drops": 0, "translation_ready": 0, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 0, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(1920, 17280)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.24s, peak_margin=-13.3dB)
- s002: [(17280, 30720)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.24s, peak_margin=-21.1dB)
- s003: [(30720, 38400)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-18.7dB)

## beta-en-1876-10323357556845456822 / formal

Reference (publisher, pending): The Northern Marianas emergency management office said that there were no damages reported in the nation.
Raw: The Northern... office.
Translation input: The Northern...

Counts: `{"captured": 6, "work_items": 6, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 4, "post_asr_drops": 1, "translation_ready": 1, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 1, "budget_pre_asr_drops": 2, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(9600, 26880)]; raw={'text': 'The Northern...', 'language': 'en', 'language_probability': 0.8829258680343628, 'avg_logprob': -0.7319146891434988, 'no_speech_prob': 0.28499606251716614, 'compression_ratio': 0.6521739130434783, 'segment_count': 1, 'duration_seconds': 1.08, 'raw_text': 'The Northern...', 'runaway_guarded': False}; rejection=
- s002: [(26880, 57600)]; raw=None; rejection=asr_budget_weak_drop
- s003: [(57600, 72960)]; raw={'text': 'office.', 'language': 'en', 'language_probability': 0.7500397562980652, 'avg_logprob': -0.9861560821533203, 'no_speech_prob': 0.5308877825737, 'compression_ratio': 0.4666666666666667, 'segment_count': 1, 'duration_seconds': 0.96, 'raw_text': 'office.', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=office, avg_logprob=-0.99, no_speech=0.53, compression=0.47)
- s004: [(72960, 97920)]; raw=None; rejection=asr_budget_weak_drop
- s005: [(97920, 107520)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.24s, peak_margin=-8.4dB)
- s006: [(107520, 122880)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.24s, peak_margin=-14.6dB)

## beta-en-1914-10335587906469246566 / formal

Reference (publisher, pending): Twentieth century research has shown that there are two pools of genetic variation: hidden and expressed.
Raw: 20th century.
Translation input: 20th century.

Counts: `{"captured": 6, "work_items": 6, "merges": 0, "asr_attempted": 1, "asr_completed": 1, "asr_missing_completion": 0, "pre_asr_drops": 5, "post_asr_drops": 0, "translation_ready": 1, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 2, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(15360, 28800)]; raw={'text': '20th century.', 'language': 'en', 'language_probability': 0.8424675464630127, 'avg_logprob': -0.791812573160444, 'no_speech_prob': 0.6019729971885681, 'compression_ratio': 0.6190476190476191, 'segment_count': 1, 'duration_seconds': 0.84, 'raw_text': '20th century.', 'runaway_guarded': False}; rejection=
- s002: [(28800, 42240)]; raw=None; rejection=asr_budget_weak_drop
- s003: [(42240, 55680)]; raw=None; rejection=asr_budget_weak_drop
- s004: [(55680, 69120)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.24s, peak_margin=-18.8dB)
- s005: [(69120, 78720)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.24s, peak_margin=-15.4dB)
- s006: [(86400, 97920)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-20.2dB)

## beta-ja-1731-10203675650837159328 / language_aware

Reference (publisher, pending): 群島や湖では、必ずしもヨットは必要ありません。
Raw: 군떡이 아님  アリマッセン
Translation input: (empty)

Counts: `{"captured": 6, "work_items": 6, "merges": 0, "asr_attempted": 3, "asr_completed": 3, "asr_missing_completion": 0, "pre_asr_drops": 3, "post_asr_drops": 3, "translation_ready": 0, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 3, "budget_pre_asr_drops": 3, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(19200, 44160)]; raw={'text': '군떡이 아님', 'language': 'ko', 'language_probability': 0.11154963076114655, 'avg_logprob': -1.2515899658203125, 'no_speech_prob': 0.35504642128944397, 'compression_ratio': 0.64, 'segment_count': 1, 'duration_seconds': 1.56, 'raw_text': '군떡이 아님', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=군떡이아님, avg_logprob=-1.25, no_speech=0.36, compression=0.64)
- s002: [(44160, 59520)]; raw=None; rejection=asr_budget_weak_drop
- s003: [(59520, 72960)]; raw={'text': '', 'language': 'en', 'language_probability': 0.19971711933612823, 'avg_logprob': 0.0, 'no_speech_prob': 0.0, 'compression_ratio': 0.0, 'segment_count': 0, 'duration_seconds': 0.84, 'raw_text': '', 'runaway_guarded': False}; rejection=empty_asr
- s004: [(72960, 86400)]; raw=None; rejection=asr_budget_weak_drop
- s005: [(86400, 99840)]; raw={'text': 'アリマッセン', 'language': 'ja', 'language_probability': 0.9328600764274597, 'avg_logprob': -1.036571078830295, 'no_speech_prob': 0.36217767000198364, 'compression_ratio': 0.6666666666666666, 'segment_count': 1, 'duration_seconds': 0.84, 'raw_text': 'アリマッセン', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=アリマッセン, avg_logprob=-1.04, no_speech=0.36, compression=0.67)
- s006: [(99840, 107520)]; raw=None; rejection=asr_budget_weak_drop

## beta-ja-1731-10203675650837159328 / legacy

Reference (publisher, pending): 群島や湖では、必ずしもヨットは必要ありません。
Raw: 그는 또야, 미...  お疲れ様でした。
Translation input: (empty)

Counts: `{"captured": 5, "work_items": 5, "merges": 0, "asr_attempted": 3, "asr_completed": 3, "asr_missing_completion": 0, "pre_asr_drops": 2, "post_asr_drops": 3, "translation_ready": 0, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 3, "budget_pre_asr_drops": 2, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(21120, 44160)]; raw={'text': '그는 또야, 미...', 'language': 'ko', 'language_probability': 0.15982645750045776, 'avg_logprob': -1.890378212928772, 'no_speech_prob': 0.3376348614692688, 'compression_ratio': 0.7, 'segment_count': 1, 'duration_seconds': 1.44, 'raw_text': '그는 또야, 미...', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=그는또야미, avg_logprob=-1.89, no_speech=0.34, compression=0.70)
- s002: [(44160, 59520)]; raw=None; rejection=asr_budget_weak_drop
- s003: [(59520, 72960)]; raw={'text': '', 'language': 'en', 'language_probability': 0.19971711933612823, 'avg_logprob': 0.0, 'no_speech_prob': 0.0, 'compression_ratio': 0.0, 'segment_count': 0, 'duration_seconds': 0.84, 'raw_text': '', 'runaway_guarded': False}; rejection=empty_asr
- s004: [(72960, 86400)]; raw=None; rejection=asr_budget_weak_drop
- s005: [(86400, 107520)]; raw={'text': 'お疲れ様でした。', 'language': 'ja', 'language_probability': 0.9537501931190491, 'avg_logprob': -1.026978886127472, 'no_speech_prob': 0.27668413519859314, 'compression_ratio': 0.6857142857142857, 'segment_count': 1, 'duration_seconds': 1.32, 'raw_text': 'お疲れ様でした。', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=お疲れ様でした, avg_logprob=-1.03, no_speech=0.28, compression=0.69)

## beta-ja-1972-10683203810610128933 / language_aware

Reference (publisher, pending): 羽を持ち、空を飛べるので、恐竜だと思っていない人も大勢います。
Raw: 羽根を持ちをそらうと 恐竜だと思う
Translation input: 羽根を持ちをそらうと 恐竜だと思う

Counts: `{"captured": 5, "work_items": 5, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 3, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 2, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(24960, 49920)]; raw={'text': '羽根を持ちをそらうと', 'language': 'ja', 'language_probability': 0.6730198264122009, 'avg_logprob': -0.5367808214255742, 'no_speech_prob': 0.4791746139526367, 'compression_ratio': 0.7692307692307693, 'segment_count': 1, 'duration_seconds': 1.56, 'raw_text': '羽根を持ちをそらうと', 'runaway_guarded': False}; rejection=
- s002: [(49920, 63360)]; raw=None; rejection=asr_budget_weak_drop
- s003: [(63360, 80640)]; raw={'text': '恐竜だと思う', 'language': 'ja', 'language_probability': 0.4099140763282776, 'avg_logprob': -0.6926794052124023, 'no_speech_prob': 0.36350497603416443, 'compression_ratio': 0.6666666666666666, 'segment_count': 1, 'duration_seconds': 1.08, 'raw_text': '恐竜だと思う', 'runaway_guarded': False}; rejection=
- s004: [(80640, 97920)]; raw=None; rejection=asr_budget_weak_drop
- s005: [(107520, 120960)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-18.6dB)

## beta-ja-1972-10683203810610128933 / legacy

Reference (publisher, pending): 羽を持ち、空を飛べるので、恐竜だと思っていない人も大勢います。
Raw: 羽根を持ちを空を飛べるので 持っていない人も
Translation input: 羽根を持ちを空を飛べるので 持っていない人も

Counts: `{"captured": 4, "work_items": 4, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 2, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 2, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(28800, 65280)]; raw={'text': '羽根を持ちを空を飛べるので', 'language': 'ja', 'language_probability': 0.8918259143829346, 'avg_logprob': -0.454726405441761, 'no_speech_prob': 0.2548649311065674, 'compression_ratio': 0.8478260869565217, 'segment_count': 1, 'duration_seconds': 2.28, 'raw_text': '羽根を持ちを空を飛べるので', 'runaway_guarded': False}; rejection=
- s002: [(65280, 80640)]; raw=None; rejection=asr_budget_weak_drop
- s003: [(80640, 99840)]; raw={'text': '持っていない人も', 'language': 'ja', 'language_probability': 0.9495720863342285, 'avg_logprob': -0.5960079299079047, 'no_speech_prob': 0.5093773603439331, 'compression_ratio': 0.75, 'segment_count': 1, 'duration_seconds': 1.2, 'raw_text': '持っていない人も', 'runaway_guarded': False}; rejection=
- s004: [(107520, 120960)]; raw=None; rejection=asr_budget_weak_drop

## beta-ja-1861-10772833950120547925 / language_aware

Reference (publisher, pending): 結果として、舞台上で出演者が大麻を吸い、劇場側も観客に参加を呼びかけています。
Raw: ケッカティし 大丈夫です 全車がタイマを3 激情がも関係 逆に参考を呼びかけています
Translation input: 全車がタイマを3 逆に参考を呼びかけています

Counts: `{"captured": 6, "work_items": 6, "merges": 0, "asr_attempted": 5, "asr_completed": 5, "asr_missing_completion": 0, "pre_asr_drops": 1, "post_asr_drops": 3, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 3, "budget_pre_asr_drops": 1, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(7680, 26880)]; raw={'text': 'ケッカティし', 'language': 'ja', 'language_probability': 0.22740252315998077, 'avg_logprob': -1.035663816663954, 'no_speech_prob': 0.5275563597679138, 'compression_ratio': 0.6666666666666666, 'segment_count': 1, 'duration_seconds': 1.2, 'raw_text': 'ケッカティし', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=ケッカティし, avg_logprob=-1.04, no_speech=0.53, compression=0.67)
- s002: [(26880, 36480)]; raw=None; rejection=asr_budget_weak_drop
- s003: [(40320, 61440)]; raw={'text': '大丈夫です', 'language': 'ja', 'language_probability': 0.9726448059082031, 'avg_logprob': -0.8087848663330078, 'no_speech_prob': 0.2274526059627533, 'compression_ratio': 0.625, 'segment_count': 1, 'duration_seconds': 1.32, 'raw_text': '大丈夫です', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=大丈夫です, avg_logprob=-0.81, no_speech=0.23, compression=0.62)
- s004: [(61440, 92160)]; raw={'text': '全車がタイマを3', 'language': 'ja', 'language_probability': 0.9396531581878662, 'avg_logprob': -0.6126802617853339, 'no_speech_prob': 0.08812519907951355, 'compression_ratio': 0.7096774193548387, 'segment_count': 1, 'duration_seconds': 1.92, 'raw_text': '全車がタイマを3', 'runaway_guarded': False}; rejection=
- s005: [(94080, 126720)]; raw={'text': '激情がも関係', 'language': 'ja', 'language_probability': 0.8766433596611023, 'avg_logprob': -0.7897862521084872, 'no_speech_prob': 0.20297186076641083, 'compression_ratio': 0.6666666666666666, 'segment_count': 1, 'duration_seconds': 2.04, 'raw_text': '激情がも関係', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=激情がも関係, avg_logprob=-0.79, no_speech=0.20, compression=0.67)
- s006: [(126720, 168960)]; raw={'text': '逆に参考を呼びかけています', 'language': 'ja', 'language_probability': 0.9829047918319702, 'avg_logprob': -0.4438668847084045, 'no_speech_prob': 0.35335567593574524, 'compression_ratio': 0.78, 'segment_count': 1, 'duration_seconds': 2.64, 'raw_text': '逆に参考を呼びかけています', 'runaway_guarded': False}; rejection=

## beta-ja-1861-10772833950120547925 / legacy

Reference (publisher, pending): 結果として、舞台上で出演者が大麻を吸い、劇場側も観客に参加を呼びかけています。
Raw: Kek katış. 部体上で 劇場側も関係 約に参考を呼びかけています
Translation input: 劇場側も関係 約に参考を呼びかけています

Counts: `{"captured": 7, "work_items": 7, "merges": 0, "asr_attempted": 4, "asr_completed": 4, "asr_missing_completion": 0, "pre_asr_drops": 3, "post_asr_drops": 2, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 2, "budget_pre_asr_drops": 3, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(9600, 26880)]; raw={'text': 'Kek katış.', 'language': 'tr', 'language_probability': 0.13940638303756714, 'avg_logprob': -0.903915673494339, 'no_speech_prob': 0.546836793422699, 'compression_ratio': 0.6, 'segment_count': 1, 'duration_seconds': 1.08, 'raw_text': 'Kek katış.', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=kekkatış, avg_logprob=-0.90, no_speech=0.55, compression=0.60)
- s002: [(26880, 36480)]; raw=None; rejection=asr_budget_weak_drop
- s003: [(42240, 61440)]; raw={'text': '部体上で', 'language': 'ja', 'language_probability': 0.9676598906517029, 'avg_logprob': -0.8358744723456246, 'no_speech_prob': 0.16188888251781464, 'compression_ratio': 0.5714285714285714, 'segment_count': 1, 'duration_seconds': 1.2, 'raw_text': '部体上で', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=部体上で, avg_logprob=-0.84, no_speech=0.16, compression=0.57)
- s004: [(61440, 74880)]; raw=None; rejection=asr_budget_weak_drop
- s005: [(74880, 88320)]; raw=None; rejection=asr_budget_weak_drop
- s006: [(96000, 126720)]; raw={'text': '劇場側も関係', 'language': 'ja', 'language_probability': 0.9136056303977966, 'avg_logprob': -0.5647355069716772, 'no_speech_prob': 0.1362430900335312, 'compression_ratio': 0.6666666666666666, 'segment_count': 1, 'duration_seconds': 1.92, 'raw_text': '劇場側も関係', 'runaway_guarded': False}; rejection=
- s007: [(126720, 168960)]; raw={'text': '約に参考を呼びかけています', 'language': 'ja', 'language_probability': 0.9829047918319702, 'avg_logprob': -0.4566135172333036, 'no_speech_prob': 0.35335567593574524, 'compression_ratio': 0.8125, 'segment_count': 1, 'duration_seconds': 2.64, 'raw_text': '約に参考を呼びかけています', 'runaway_guarded': False}; rejection=

## beta-ko-1742-10505940208824594418 / legacy

Reference (publisher, pending): 홍콩 섬은 홍콩 영토에 홍콩이라는 이름을 부여한 곳이자 많은 관광객들이 주안점으로 여기는 곳이다.
Raw: 홍콩사는 홍콩 영토의 홍콩이라는 이름을 부위한 곳 시작 많은 관광객들이 추워한 점으로
Translation input: 홍콩사는 홍콩 영토의 홍콩이라는 이름을 부위한 곳 시작 많은 관광객들이 추워한 점으로

Counts: `{"captured": 4, "work_items": 4, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 2, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 1, "forced_capture_cuts": 2}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(0, 9600)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-18.6dB)
- s002: [(17280, 67200)]; raw={'text': '홍콩사는 홍콩 영토의 홍콩이라는 이름을', 'language': 'ko', 'language_probability': 0.9978874325752258, 'avg_logprob': -0.30389022678136823, 'no_speech_prob': 0.018381508067250252, 'compression_ratio': 1.0377358490566038, 'segment_count': 1, 'duration_seconds': 3.12, 'raw_text': '홍콩사는 홍콩 영토의 홍콩이라는 이름을', 'runaway_guarded': False}; rejection=
- s003: [(67200, 115200)]; raw={'text': '부위한 곳 시작 많은 관광객들이 추워한 점으로', 'language': 'ko', 'language_probability': 0.9885541796684265, 'avg_logprob': -0.5941620137956407, 'no_speech_prob': 0.10354537516832352, 'compression_ratio': 0.8513513513513513, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': '부위한 곳 시작 많은 관광객들이 추워한 점으로', 'runaway_guarded': False}; rejection=
- s004: [(115200, 134400)]; raw=None; rejection=asr_budget_weak_drop

## beta-ko-1742-10505940208824594418 / language_aware

Reference (publisher, pending): 홍콩 섬은 홍콩 영토에 홍콩이라는 이름을 부여한 곳이자 많은 관광객들이 주안점으로 여기는 곳이다.
Raw: 홍콩섬은 홍콩영토의 홍콩이라는 이름을 부여한 곳이자 많은 관광객들이 주한점으로 여기는 곳이다.
Translation input: 홍콩섬은 홍콩영토의 홍콩이라는 이름을 부여한 곳이자 많은 관광객들이 주한점으로 여기는 곳이다.

Counts: `{"captured": 3, "work_items": 3, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 1, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 0, "forced_capture_cuts": 1}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(0, 9600)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-18.6dB)
- s002: [(15360, 88320)]; raw={'text': '홍콩섬은 홍콩영토의 홍콩이라는 이름을 부여한 곳이자 많은', 'language': 'ko', 'language_probability': 0.9826695919036865, 'avg_logprob': -0.25035008043050766, 'no_speech_prob': 0.20448391139507294, 'compression_ratio': 1.0253164556962024, 'segment_count': 1, 'duration_seconds': 4.56, 'raw_text': '홍콩섬은 홍콩영토의 홍콩이라는 이름을 부여한 곳이자 많은', 'runaway_guarded': False}; rejection=
- s003: [(88320, 134400)]; raw={'text': '관광객들이 주한점으로 여기는 곳이다.', 'language': 'ko', 'language_probability': 0.9972007274627686, 'avg_logprob': -0.37025585969289143, 'no_speech_prob': 0.04568663612008095, 'compression_ratio': 0.8253968253968254, 'segment_count': 1, 'duration_seconds': 2.88, 'raw_text': '관광객들이 주한점으로 여기는 곳이다.', 'runaway_guarded': False}; rejection=

## beta-ko-1907-1053553381405565115 / language_aware

Reference (publisher, pending): 교전이 발발한 직후 영국은 독일에 대한 해상 봉쇄를 시작한다.
Raw: 교전이 발발한 직후 영국은 독일에 대한 해상 봉쇄를 시...
Translation input: 교전이 발발한 직후 영국은 독일에 대한 해상 봉쇄를 시...

Counts: `{"captured": 2, "work_items": 2, "merges": 0, "asr_attempted": 1, "asr_completed": 1, "asr_missing_completion": 0, "pre_asr_drops": 1, "post_asr_drops": 0, "translation_ready": 1, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 1, "forced_capture_cuts": 1}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(30720, 103680)]; raw={'text': '교전이 발발한 직후 영국은 독일에 대한 해상 봉쇄를 시...', 'language': 'ko', 'language_probability': 0.9513195157051086, 'avg_logprob': -0.33889767196443343, 'no_speech_prob': 0.4284299612045288, 'compression_ratio': 0.8953488372093024, 'segment_count': 1, 'duration_seconds': 4.56, 'raw_text': '교전이 발발한 직후 영국은 독일에 대한 해상 봉쇄를 시...', 'runaway_guarded': False}; rejection=
- s002: [(103680, 120960)]; raw=None; rejection=asr_budget_weak_drop

## beta-ko-1907-1053553381405565115 / legacy

Reference (publisher, pending): 교전이 발발한 직후 영국은 독일에 대한 해상 봉쇄를 시작한다.
Raw: 교전이 발발한 직구 영국은 보기를 해상 봉세를 시작한다.
Translation input: 교전이 발발한 직구 영국은 보기를

Counts: `{"captured": 2, "work_items": 2, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 0, "post_asr_drops": 1, "translation_ready": 1, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 1, "budget_pre_asr_drops": 0, "forced_capture_cuts": 1}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(32640, 80640)]; raw={'text': '교전이 발발한 직구 영국은 보기를', 'language': 'ko', 'language_probability': 0.9822297096252441, 'avg_logprob': -0.42809478007256985, 'no_speech_prob': 0.14818014204502106, 'compression_ratio': 0.8363636363636363, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': '교전이 발발한 직구 영국은 보기를', 'runaway_guarded': False}; rejection=
- s002: [(80640, 120960)]; raw={'text': '해상 봉세를 시작한다.', 'language': 'ko', 'language_probability': 0.981846034526825, 'avg_logprob': -0.8248303830623627, 'no_speech_prob': 0.2732621729373932, 'compression_ratio': 0.7317073170731707, 'segment_count': 1, 'duration_seconds': 2.52, 'raw_text': '해상 봉세를 시작한다.', 'runaway_guarded': False}; rejection=weak_candidate_low_asr_confidence (text=해상봉세를시작한다, avg_logprob=-0.82, no_speech=0.27, compression=0.73)

## beta-ko-1894-11320272182475458144 / language_aware

Reference (publisher, pending): 커리는 약용 식물과 향신료를 기본으로 하여 고기나 채소를 곁들이는 요리입니다.
Raw: 컬이는 야경식물과 향신료를 기보드로 하여
Translation input: 컬이는 야경식물과 향신료를 기보드로 하여

Counts: `{"captured": 4, "work_items": 5, "merges": 1, "asr_attempted": 1, "asr_completed": 1, "asr_missing_completion": 0, "pre_asr_drops": 2, "post_asr_drops": 0, "translation_ready": 1, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 1, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(30720, 94080)]; raw={'text': '컬이는 야경식물과 향신료를 기보드로 하여', 'language': 'ko', 'language_probability': 0.9726569652557373, 'avg_logprob': -0.35277672789313574, 'no_speech_prob': 0.2018395960330963, 'compression_ratio': 0.8405797101449275, 'segment_count': 1, 'duration_seconds': 3.96, 'raw_text': '컬이는 야경식물과 향신료를 기보드로 하여', 'runaway_guarded': False}; rejection=
- s002: [(94080, 117120)]; raw=None; rejection=None
- s003: [(117120, 140160)]; raw=None; rejection=None
- s004: [(94080, 140160)]; raw=None; rejection=asr_budget_weak_drop
- s005: [(168960, 182400)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-20.8dB)

## beta-ko-1894-11320272182475458144 / legacy

Reference (publisher, pending): 커리는 약용 식물과 향신료를 기본으로 하여 고기나 채소를 곁들이는 요리입니다.
Raw: 털이는 야경식물과 향신료를 기부 고기나 채소를 적..
Translation input: 털이는 야경식물과 향신료를 기부 고기나 채소를 적..

Counts: `{"captured": 5, "work_items": 5, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 3, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 2, "forced_capture_cuts": 1}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(32640, 80640)]; raw={'text': '털이는 야경식물과 향신료를 기부', 'language': 'ko', 'language_probability': 0.9765118360519409, 'avg_logprob': -0.5940740836991204, 'no_speech_prob': 0.2178107053041458, 'compression_ratio': 0.8035714285714286, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': '털이는 야경식물과 향신료를 기부', 'runaway_guarded': False}; rejection=
- s002: [(80640, 94080)]; raw=None; rejection=asr_budget_weak_drop
- s003: [(94080, 117120)]; raw={'text': '고기나 채소를 적..', 'language': 'ko', 'language_probability': 0.9693965315818787, 'avg_logprob': -0.5917357314716686, 'no_speech_prob': 0.15835727751255035, 'compression_ratio': 0.6944444444444444, 'segment_count': 1, 'duration_seconds': 1.44, 'raw_text': '고기나 채소를 적..', 'runaway_guarded': False}; rejection=
- s004: [(117120, 140160)]; raw=None; rejection=asr_budget_weak_drop
- s005: [(170880, 182400)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-20.8dB)

## beta-ru-1704-10021068571959461962 / language_aware

Reference (publisher, pending): В 1990 году он был добавлен в список всемирного наследия, находящегося под угрозой из-за опасности со стороны песков пустыни.
Raw: 1990 году он был добавлен в списк в Семерного наследия. находящуюся по догрозе із опасності со стороны пізков впустині.
Translation input: 1990 году он был добавлен в списк в Семерного наследия.

Counts: `{"captured": 4, "work_items": 4, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 2, "post_asr_drops": 0, "translation_ready": 1, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 1, "all_post_inference_rejections": 1, "budget_pre_asr_drops": 1, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(3840, 17280)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.24s, peak_margin=-11.9dB)
- s002: [(17280, 84480)]; raw={'text': '1990 году он был добавлен в списк в Семерного наследия.', 'language': 'ru', 'language_probability': 0.9398428797721863, 'avg_logprob': -0.46190784091041204, 'no_speech_prob': 0.34320956468582153, 'compression_ratio': 1.103448275862069, 'segment_count': 1, 'duration_seconds': 4.2, 'raw_text': '1990 году он был добавлен в списк в Семерного наследия.', 'runaway_guarded': False}; rejection=
- s003: [(84480, 153600)]; raw={'text': 'находящуюся по догрозе із опасності со стороны пізков впустині.', 'language': 'uk', 'language_probability': 0.9227538704872131, 'avg_logprob': -0.6377697395426887, 'no_speech_prob': 0.013507156632840633, 'compression_ratio': 1.231578947368421, 'segment_count': 1, 'duration_seconds': 4.32, 'raw_text': 'находящуюся по догрозе із опасності со стороны пізков впустині.', 'runaway_guarded': False}; rejection=language_mismatch:uk->ru:prob=0.92:threshold=0.60
- s004: [(153600, 165120)]; raw=None; rejection=asr_budget_weak_drop

## beta-ru-1704-10021068571959461962 / legacy

Reference (publisher, pending): В 1990 году он был добавлен в список всемирного наследия, находящегося под угрозой из-за опасности со стороны песков пустыни.
Raw: 1990 году он был добавлен в списку в Семир. Находящуюся по догрозе із опасності со стороны
Translation input: 1990 году он был добавлен в списку в Семир.

Counts: `{"captured": 6, "work_items": 6, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 4, "post_asr_drops": 0, "translation_ready": 1, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 1, "all_post_inference_rejections": 1, "budget_pre_asr_drops": 2, "forced_capture_cuts": 2}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(5760, 17280)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.24s, peak_margin=-11.9dB)
- s002: [(17280, 67200)]; raw={'text': '1990 году он был добавлен в списку в Семир.', 'language': 'ru', 'language_probability': 0.9089387059211731, 'avg_logprob': -0.6286608752082375, 'no_speech_prob': 0.5742719769477844, 'compression_ratio': 0.9733333333333334, 'segment_count': 1, 'duration_seconds': 3.12, 'raw_text': '1990 году он был добавлен в списку в Семир.', 'runaway_guarded': False}; rejection=
- s003: [(67200, 84480)]; raw=None; rejection=asr_budget_weak_drop
- s004: [(84480, 132480)]; raw={'text': 'Находящуюся по догрозе із опасності со стороны', 'language': 'uk', 'language_probability': 0.8792120814323425, 'avg_logprob': -0.7176055401563645, 'no_speech_prob': 0.16131049394607544, 'compression_ratio': 1.1025641025641026, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': 'Находящуюся по догрозе із опасності со стороны', 'runaway_guarded': False}; rejection=language_mismatch:uk->ru:prob=0.88:threshold=0.60
- s005: [(132480, 153600)]; raw=None; rejection=asr_budget_weak_drop
- s006: [(153600, 165120)]; raw=None; rejection=weak_fast_pre_asr_low_confidence_tiny_voice (voice=0.12s, peak_margin=-22.5dB)

## beta-ru-1757-10040813106556859083 / legacy

Reference (publisher, pending): Только мутации в клетках зародышевой линии могут передаваться далее детям, в то время как мутации где-то ещё могут привести к гибели клеток или раку.
Raw: Только мутации в клетках зарода шеволений могут трёхать. до вас и далее. то время как мутаться где-то еще могут привести гиблик. и раку.
Translation input: Только мутации в клетках зарода шеволений могут трёхать. то время как мутаться где-то еще могут привести гиблик. и раку.

Counts: `{"captured": 4, "work_items": 4, "merges": 0, "asr_attempted": 4, "asr_completed": 4, "asr_missing_completion": 0, "pre_asr_drops": 0, "post_asr_drops": 1, "translation_ready": 3, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 1, "budget_pre_asr_drops": 0, "forced_capture_cuts": 2}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(24960, 72960)]; raw={'text': 'Только мутации в клетках зарода шеволений могут трёхать.', 'language': 'ru', 'language_probability': 0.9969797730445862, 'avg_logprob': -0.6091908009155936, 'no_speech_prob': 0.006821800488978624, 'compression_ratio': 1.1555555555555554, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': 'Только мутации в клетках зарода шеволений могут трёхать.', 'runaway_guarded': False}; rejection=
- s002: [(72960, 97920)]; raw={'text': 'до вас и далее.', 'language': 'ru', 'language_probability': 0.9867820143699646, 'avg_logprob': -1.1753049790859222, 'no_speech_prob': 0.08651968836784363, 'compression_ratio': 0.7027027027027027, 'segment_count': 1, 'duration_seconds': 1.56, 'raw_text': 'до вас и далее.', 'runaway_guarded': False}; rejection=global_asr_low_logprob_short avg_logprob=-1.18
- s003: [(97920, 145920)]; raw={'text': 'то время как мутаться где-то еще могут привести гиблик.', 'language': 'ru', 'language_probability': 0.9962904453277588, 'avg_logprob': -0.4778821127755301, 'no_speech_prob': 0.014655045233666897, 'compression_ratio': 1.1627906976744187, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': 'то время как мутаться где-то еще могут привести гиблик.', 'runaway_guarded': False}; rejection=
- s004: [(145920, 168960)]; raw={'text': 'и раку.', 'language': 'ru', 'language_probability': 0.9524344205856323, 'avg_logprob': -0.772489570081234, 'no_speech_prob': 0.18000376224517822, 'compression_ratio': 0.5714285714285714, 'segment_count': 1, 'duration_seconds': 1.44, 'raw_text': 'и раку.', 'runaway_guarded': False}; rejection=

## beta-ru-1757-10040813106556859083 / language_aware

Reference (publisher, pending): Только мутации в клетках зародышевой линии могут передаваться далее детям, в то время как мутации где-то ещё могут привести к гибели клеток или раку.
Raw: Только мутации в клетках зародышевой линии могут передаваться далее детям. то время как мутация где-то еще могут привести гибликлеток или раку.
Translation input: Только мутации в клетках зародышевой линии могут передаваться далее детям. то время как мутация где-то еще могут привести гибликлеток или раку.

Counts: `{"captured": 2, "work_items": 2, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 0, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 0, "forced_capture_cuts": 0}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(23040, 97920)]; raw={'text': 'Только мутации в клетках зародышевой линии могут передаваться далее детям.', 'language': 'ru', 'language_probability': 0.9988514184951782, 'avg_logprob': -0.37710446004684156, 'no_speech_prob': 0.0017884981352835894, 'compression_ratio': 1.2777777777777777, 'segment_count': 1, 'duration_seconds': 4.68, 'raw_text': 'Только мутации в клетках зародышевой линии могут передаваться далее детям.', 'runaway_guarded': False}; rejection=
- s002: [(97920, 168960)]; raw={'text': 'то время как мутация где-то еще могут привести гибликлеток или раку.', 'language': 'ru', 'language_probability': 0.9990968704223633, 'avg_logprob': -0.29324292695080795, 'no_speech_prob': 0.0012638160260394216, 'compression_ratio': 1.2653061224489797, 'segment_count': 1, 'duration_seconds': 4.44, 'raw_text': 'то время как мутация где-то еще могут привести гибликлеток или раку.', 'runaway_guarded': False}; rejection=

## beta-ru-1861-10276863687632229120 / language_aware

Reference (publisher, pending): В результате актёры курят косяки с марихуаной на сцене, и сам театр поощряет публику присоединиться.
Raw: В результаті актіори курят касікі смерехуани на сцені і сам театр. ваше реак публику присоединится.
Translation input: В результаті актіори курят касікі смерехуани на сцені і сам театр. ваше реак публику присоединится.

Counts: `{"captured": 2, "work_items": 2, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 0, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 0, "forced_capture_cuts": 1}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(1920, 74880)]; raw={'text': 'В результаті актіори курят касікі смерехуани на сцені і сам театр.', 'language': 'uk', 'language_probability': 0.5072683691978455, 'avg_logprob': -0.6202411074792186, 'no_speech_prob': 0.015450293198227882, 'compression_ratio': 1.2736842105263158, 'segment_count': 1, 'duration_seconds': 4.56, 'raw_text': 'В результаті актіори курят касікі смерехуани на сцені і сам театр.', 'runaway_guarded': False}; rejection=
- s002: [(74880, 109440)]; raw={'text': 'ваше реак публику присоединится.', 'language': 'ru', 'language_probability': 0.9683688879013062, 'avg_logprob': -0.7943294383585453, 'no_speech_prob': 0.08808835595846176, 'compression_ratio': 0.9375, 'segment_count': 1, 'duration_seconds': 2.16, 'raw_text': 'ваше реак публику присоединится.', 'runaway_guarded': False}; rejection=

## beta-ru-1861-10276863687632229120 / legacy

Reference (publisher, pending): В результате актёры курят косяки с марихуаной на сцене, и сам театр поощряет публику присоединиться.
Raw: В результате актёры курят кассики с мариханами. на сцене и сам театр пащает публику присоединения.
Translation input: В результате актёры курят кассики с мариханами. на сцене и сам театр пащает публику присоединения.

Counts: `{"captured": 3, "work_items": 3, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 1, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 1, "forced_capture_cuts": 2}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(3840, 51840)]; raw={'text': 'В результате актёры курят кассики с мариханами.', 'language': 'ru', 'language_probability': 0.7313090562820435, 'avg_logprob': -0.47366959708077566, 'no_speech_prob': 0.02568277344107628, 'compression_ratio': 1.1153846153846154, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': 'В результате актёры курят кассики с мариханами.', 'runaway_guarded': False}; rejection=
- s002: [(51840, 99840)]; raw={'text': 'на сцене и сам театр пащает публику присоединения.', 'language': 'ru', 'language_probability': 0.846953809261322, 'avg_logprob': -0.44754398646561994, 'no_speech_prob': 0.650562584400177, 'compression_ratio': 1.15, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': 'на сцене и сам театр пащает публику присоединения.', 'runaway_guarded': False}; rejection=
- s003: [(99840, 109440)]; raw=None; rejection=asr_budget_weak_drop

## beta-ru-1885-10312175978910673333 / language_aware

Reference (publisher, pending): Между 10:00 и 11:00 вечера по горному времени заключенные устроили пожар во дворе.
Raw: Между десятью и одиннадцати вечера по горному времени заключённый строили пожар во дворе.
Translation input: Между десятью и одиннадцати вечера по горному времени заключённый строили пожар во дворе.

Counts: `{"captured": 2, "work_items": 2, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 0, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 0, "forced_capture_cuts": 1}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(7680, 80640)]; raw={'text': 'Между десятью и одиннадцати вечера по горному времени заключённый', 'language': 'ru', 'language_probability': 0.9932223558425903, 'avg_logprob': -0.45198778266256506, 'no_speech_prob': 0.028593704104423523, 'compression_ratio': 1.22, 'segment_count': 1, 'duration_seconds': 4.56, 'raw_text': 'Между десятью и одиннадцати вечера по горному времени заключённый', 'runaway_guarded': False}; rejection=
- s002: [(80640, 107520)]; raw={'text': 'строили пожар во дворе.', 'language': 'ru', 'language_probability': 0.9686986804008484, 'avg_logprob': -0.6678409468043934, 'no_speech_prob': 0.1329883337020874, 'compression_ratio': 0.875, 'segment_count': 1, 'duration_seconds': 1.68, 'raw_text': 'строили пожар во дворе.', 'runaway_guarded': False}; rejection=

## beta-ru-1885-10312175978910673333 / legacy

Reference (publisher, pending): Между 10:00 и 11:00 вечера по горному времени заключенные устроили пожар во дворе.
Raw: Между десятью и одиннадцати вечера по гарному. Время заключенные устроили пожар в адвари.
Translation input: Между десятью и одиннадцати вечера по гарному. Время заключенные устроили пожар в адвари.

Counts: `{"captured": 2, "work_items": 2, "merges": 0, "asr_attempted": 2, "asr_completed": 2, "asr_missing_completion": 0, "pre_asr_drops": 0, "post_asr_drops": 0, "translation_ready": 2, "raw_queue_drops": 0, "unresolved_work_items": 0, "translation_language_gate_drops": 0, "all_post_inference_rejections": 0, "budget_pre_asr_drops": 0, "forced_capture_cuts": 1}`

Segments (WAV frame intervals; exact PCM verified):

- s001: [(9600, 57600)]; raw={'text': 'Между десятью и одиннадцати вечера по гарному.', 'language': 'ru', 'language_probability': 0.9841657876968384, 'avg_logprob': -0.3459665367477818, 'no_speech_prob': 0.03259563446044922, 'compression_ratio': 1.0625, 'segment_count': 1, 'duration_seconds': 3.0, 'raw_text': 'Между десятью и одиннадцати вечера по гарному.', 'runaway_guarded': False}; rejection=
- s002: [(57600, 107520)]; raw={'text': 'Время заключенные устроили пожар в адвари.', 'language': 'ru', 'language_probability': 0.9938918352127075, 'avg_logprob': -0.5421067774295807, 'no_speech_prob': 0.011948956176638603, 'compression_ratio': 1.0129870129870129, 'segment_count': 1, 'duration_seconds': 3.12, 'raw_text': 'Время заключенные устроили пожар в адвари.', 'runaway_guarded': False}; rejection=
