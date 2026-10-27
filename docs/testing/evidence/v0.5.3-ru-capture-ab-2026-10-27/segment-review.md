# RU capture matrix — local segment review

Runtime a67a6563 / 645c6ace unchanged; 2 known public FLEURS recordings, not holdouts or game audio. Human bilingual review pending.

Frame intervals are half-open at 16000 Hz. Stream frames include paired silence/order. Original-WAV frames are intersections with the source recording. No word-level gold timestamps are available.

All 16 result.json files retain actual configs, every activity window, captures, work items, normalization and shutdown status. Full events.jsonl and emitted WAVs remain in build/multilingual-online/ru-max-only-20261027 (hashes in artifact-index.json).

5/100 ms labels are requested sleep intervals after processing, not achieved QTimer periods. Peak RSS is sampled at 50 ms; ASR CPU is process CPU during the call and includes observation overhead.

## r1-tick5-max4.5

Replay CPU 8.8125s; peak sampled RSS 343.98 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "retained": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "translation_input": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "non_russian_detected": ["nl"], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 124800]] | [(3840, 76800)] | 达到最长 4.5s / 5760 | Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные. | ru / 0.961456 | Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные. | 1031.79 / 2.0469 / 341.55 | 7.29591354084414 |
| s002 | [[124800, 149760]] | [(76800, 101760)] | 静音结束/尾音下降 / 0 | het seise ijoud. | nl / 0.191841 | 语言置信度 0.19 < 0.35 | 962.07 / 1.9062 / 342.27 | 10.88482644748838 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 977.83 / 1.9375 / 343.75 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 991.78 / 1.9375 / 343.98 | 0.0 |

## r1-tick5-max3

Replay CPU 8.7969s; peak sampled RSS 343.20 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): К согласной ядерному управлению Японии на заводе. и полябно ружина радиоактивной цези и йод.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "retained": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "translation_input": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 99840]] | [(3840, 51840)] | 达到最长 3s / 5760 | К согласной ядерному управлению Японии на заводе. | ru / 0.946306 | К согласной ядерному управлению Японии на заводе. | 981.23 / 1.9531 / 341.07 | 7.707385918457511 |
| s002 | [[99840, 149760]] | [(51840, 101760)] | 静音结束/尾音下降 / 0 | и полябно ружина радиоактивной цези и йод. | ru / 0.989847 | и полябно ружина радиоактивной цези и йод. | 1006.28 / 2.0312 / 341.44 | 8.233995488744341 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через комаров болезть затем передаяться

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 975.59 / 1.9531 / 342.95 | 0.0 |
| s004 | [[245760, 293760]] | [(50560, 98560)] | 达到最长 3s / 0 | от которых через комаров болезть затем передаяться | ru / 0.901237 | от которых через комаров болезть затем передаяться | 969.06 / 1.8594 / 343.20 | 0.0 |
| s005 | [[293760, 307200]] | [(98560, 112000)] | 静音结束/尾音下降 / 0 |  | N/A | asr_budget_weak_drop | not submitted | N/A |

## r1-tick5-max3.5

Replay CPU 9.2500s; peak sampled RSS 344.13 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): Соклассный ядерному управлению Японии, на заводе были обнаружены. на радиоактивной цизи иет.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "retained": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "translation_input": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 109440]] | [(3840, 61440)] | 达到最长 3.5s / 5760 | Соклассный ядерному управлению Японии, на заводе были обнаружены. | ru / 0.941048 | Соклассный ядерному управлению Японии, на заводе были обнаружены. | 1019.43 / 2.0312 / 341.83 | 7.481458667115501 |
| s002 | [[109440, 149760]] | [(61440, 101760)] | 静音结束/尾音下降 / 0 | на радиоактивной цизи иет. | ru / 0.986247 | на радиоактивной цизи иет. | 1026.55 / 2.1562 / 342.02 | 8.773460876214752 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 971.78 / 1.9062 / 343.13 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 987.48 / 1.9688 / 344.13 | 0.0 |

## r1-tick5-max4

Replay CPU 8.9375s; peak sampled RSS 344.61 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): К согласной ядерному управлению Японии на заводе были обнаружены радио активной цези иет.

Automatic suspicion flags: `{"raw": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "retained": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "translation_input": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 117120]] | [(3840, 69120)] | 达到最长 4s / 5760 | К согласной ядерному управлению Японии на заводе были обнаружены радио | ru / 0.962890 | К согласной ядерному управлению Японии на заводе были обнаружены радио | 1009.56 / 2.0312 / 342.24 | 7.261685569549094 |
| s002 | [[117120, 149760]] | [(69120, 101760)] | 静音结束/尾音下降 / 0 | активной цези иет. | ru / 0.969846 | активной цези иет. | 973.38 / 1.9375 / 342.74 | 9.859809019745633 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 966.75 / 1.8906 / 308.61 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 990.43 / 1.9844 / 344.61 | 0.0 |

## r1-tick100-max4.5

Replay CPU 8.8906s; peak sampled RSS 344.63 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "retained": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "translation_input": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "non_russian_detected": ["nl"], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 124800]] | [(3840, 76800)] | 达到最长 4.5s / 5760 | Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные. | ru / 0.961456 | Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные. | 1013.26 / 2.0312 / 342.44 | 7.29591354084414 |
| s002 | [[124800, 149760]] | [(76800, 101760)] | 静音结束/尾音下降 / 0 | het seise ijoud. | nl / 0.191841 | 语言置信度 0.19 < 0.35 | 966.82 / 1.9375 / 342.14 | 10.88482644748838 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 971.09 / 1.9062 / 343.37 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 983.89 / 1.9688 / 344.63 | 0.0 |

## r1-tick100-max3

Replay CPU 9.0469s; peak sampled RSS 343.71 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): К согласной ядерному управлению Японии на заводе. и полябно ружина радиоактивной цези и йод.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "retained": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "translation_input": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 99840]] | [(3840, 51840)] | 达到最长 3s / 5760 | К согласной ядерному управлению Японии на заводе. | ru / 0.946306 | К согласной ядерному управлению Японии на заводе. | 992.99 / 1.9844 / 341.35 | 7.707385918457511 |
| s002 | [[99840, 149760]] | [(51840, 101760)] | 静音结束/尾音下降 / 0 | и полябно ружина радиоактивной цези и йод. | ru / 0.989847 | и полябно ружина радиоактивной цези и йод. | 1008.74 / 2.0156 / 330.92 | 8.233995488744341 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через комаров болезть затем передаяться

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 975.94 / 1.9219 / 334.20 | 0.0 |
| s004 | [[245760, 293760]] | [(50560, 98560)] | 达到最长 3s / 0 | от которых через комаров болезть затем передаяться | ru / 0.901237 | от которых через комаров болезть затем передаяться | 984.99 / 1.9375 / 343.71 | 0.0 |
| s005 | [[293760, 307200]] | [(98560, 112000)] | 静音结束/尾音下降 / 0 |  | N/A | asr_budget_weak_drop | not submitted | N/A |

## r1-tick100-max3.5

Replay CPU 8.9531s; peak sampled RSS 343.72 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): Соклассный ядерному управлению Японии, на заводе были обнаружены. на радиоактивной цизи иет.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "retained": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "translation_input": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 109440]] | [(3840, 61440)] | 达到最长 3.5s / 5760 | Соклассный ядерному управлению Японии, на заводе были обнаружены. | ru / 0.941048 | Соклассный ядерному управлению Японии, на заводе были обнаружены. | 1013.56 / 2.0312 / 341.25 | 7.481458667115501 |
| s002 | [[109440, 149760]] | [(61440, 101760)] | 静音结束/尾音下降 / 0 | на радиоактивной цизи иет. | ru / 0.986247 | на радиоактивной цизи иет. | 973.35 / 1.9375 / 341.66 | 8.773460876214752 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 966.07 / 1.8906 / 342.83 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 990.24 / 1.9531 / 343.72 | 0.0 |

## r1-tick100-max4

Replay CPU 8.8438s; peak sampled RSS 344.39 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): К согласной ядерному управлению Японии на заводе были обнаружены радио активной цези иет.

Automatic suspicion flags: `{"raw": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "retained": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "translation_input": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 117120]] | [(3840, 69120)] | 达到最长 4s / 5760 | К согласной ядерному управлению Японии на заводе были обнаружены радио | ru / 0.962890 | К согласной ядерному управлению Японии на заводе были обнаружены радио | 1026.05 / 2.0312 / 341.99 | 7.261685569549094 |
| s002 | [[117120, 149760]] | [(69120, 101760)] | 静音结束/尾音下降 / 0 | активной цези иет. | ru / 0.969846 | активной цези иет. | 962.78 / 1.9062 / 342.29 | 9.859809019745633 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 977.72 / 1.9531 / 343.52 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 997.58 / 1.9844 / 344.39 | 0.0 |

## r2-tick100-max4

Replay CPU 8.7188s; peak sampled RSS 343.87 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): К согласной ядерному управлению Японии на заводе были обнаружены радио активной цези иет.

Automatic suspicion flags: `{"raw": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "retained": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "translation_input": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 117120]] | [(3840, 69120)] | 达到最长 4s / 5760 | К согласной ядерному управлению Японии на заводе были обнаружены радио | ru / 0.962890 | К согласной ядерному управлению Японии на заводе были обнаружены радио | 989.32 / 1.9844 / 341.65 | 7.261685569549094 |
| s002 | [[117120, 149760]] | [(69120, 101760)] | 静音结束/尾音下降 / 0 | активной цези иет. | ru / 0.969846 | активной цези иет. | 957.25 / 1.8594 / 341.97 | 9.859809019745633 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 974.18 / 1.9375 / 343.87 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 1000.25 / 1.9219 / 343.81 | 0.0 |

## r2-tick100-max3.5

Replay CPU 8.9062s; peak sampled RSS 345.07 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): Соклассный ядерному управлению Японии, на заводе были обнаружены. на радиоактивной цизи иет.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "retained": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "translation_input": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 109440]] | [(3840, 61440)] | 达到最长 3.5s / 5760 | Соклассный ядерному управлению Японии, на заводе были обнаружены. | ru / 0.941048 | Соклассный ядерному управлению Японии, на заводе были обнаружены. | 1024.77 / 2.0469 / 341.54 | 7.481458667115501 |
| s002 | [[109440, 149760]] | [(61440, 101760)] | 静音结束/尾音下降 / 0 | на радиоактивной цизи иет. | ru / 0.986247 | на радиоактивной цизи иет. | 969.36 / 1.9375 / 342.84 | 8.773460876214752 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 983.09 / 1.9531 / 343.31 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 987.62 / 2.0000 / 345.07 | 0.0 |

## r2-tick100-max3

Replay CPU 8.6875s; peak sampled RSS 343.22 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): К согласной ядерному управлению Японии на заводе. и полябно ружина радиоактивной цези и йод.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "retained": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "translation_input": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 99840]] | [(3840, 51840)] | 达到最长 3s / 5760 | К согласной ядерному управлению Японии на заводе. | ru / 0.946306 | К согласной ядерному управлению Японии на заводе. | 982.65 / 1.9531 / 341.11 | 7.707385918457511 |
| s002 | [[99840, 149760]] | [(51840, 101760)] | 静音结束/尾音下降 / 0 | и полябно ружина радиоактивной цези и йод. | ru / 0.989847 | и полябно ружина радиоактивной цези и йод. | 990.96 / 1.9062 / 342.65 | 8.233995488744341 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через комаров болезть затем передаяться

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 960.07 / 1.9375 / 343.22 | 0.0 |
| s004 | [[245760, 293760]] | [(50560, 98560)] | 达到最长 3s / 0 | от которых через комаров болезть затем передаяться | ru / 0.901237 | от которых через комаров болезть затем передаяться | 965.74 / 1.9062 / 343.22 | 0.0 |
| s005 | [[293760, 307200]] | [(98560, 112000)] | 静音结束/尾音下降 / 0 |  | N/A | asr_budget_weak_drop | not submitted | N/A |

## r2-tick100-max4.5

Replay CPU 8.9375s; peak sampled RSS 344.04 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "retained": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "translation_input": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "non_russian_detected": ["nl"], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 124800]] | [(3840, 76800)] | 达到最长 4.5s / 5760 | Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные. | ru / 0.961456 | Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные. | 1019.02 / 2.1094 / 341.93 | 7.29591354084414 |
| s002 | [[124800, 149760]] | [(76800, 101760)] | 静音结束/尾音下降 / 0 | het seise ijoud. | nl / 0.191841 | 语言置信度 0.19 < 0.35 | 969.18 / 1.9219 / 341.79 | 10.88482644748838 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 969.01 / 1.9375 / 343.29 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 984.10 / 1.9688 / 344.04 | 0.0 |

## r2-tick5-max4

Replay CPU 8.7969s; peak sampled RSS 344.11 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): К согласной ядерному управлению Японии на заводе были обнаружены радио активной цези иет.

Automatic suspicion flags: `{"raw": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "retained": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "translation_input": {"radioactivity": false, "cesium_suspected": true, "iodine_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 117120]] | [(3840, 69120)] | 达到最长 4s / 5760 | К согласной ядерному управлению Японии на заводе были обнаружены радио | ru / 0.962890 | К согласной ядерному управлению Японии на заводе были обнаружены радио | 1008.05 / 1.9844 / 341.26 | 7.261685569549094 |
| s002 | [[117120, 149760]] | [(69120, 101760)] | 静音结束/尾音下降 / 0 | активной цези иет. | ru / 0.969846 | активной цези иет. | 958.93 / 1.9062 / 341.42 | 9.859809019745633 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 980.80 / 1.9531 / 343.68 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 984.17 / 1.9531 / 344.11 | 0.0 |

## r2-tick5-max3.5

Replay CPU 9.0781s; peak sampled RSS 343.14 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): Соклассный ядерному управлению Японии, на заводе были обнаружены. на радиоактивной цизи иет.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "retained": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "translation_input": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 109440]] | [(3840, 61440)] | 达到最长 3.5s / 5760 | Соклассный ядерному управлению Японии, на заводе были обнаружены. | ru / 0.941048 | Соклассный ядерному управлению Японии, на заводе были обнаружены. | 1013.20 / 2.0312 / 340.98 | 7.481458667115501 |
| s002 | [[109440, 149760]] | [(61440, 101760)] | 静音结束/尾音下降 / 0 | на радиоактивной цизи иет. | ru / 0.986247 | на радиоактивной цизи иет. | 987.87 / 1.9219 / 341.27 | 8.773460876214752 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 971.00 / 1.9375 / 342.85 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 994.65 / 1.9844 / 343.14 | 0.0 |

## r2-tick5-max3

Replay CPU 8.7031s; peak sampled RSS 343.97 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): К согласной ядерному управлению Японии на заводе. и полябно ружина радиоактивной цези и йод.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "retained": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "translation_input": {"radioactivity": true, "cesium_suspected": true, "iodine_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 99840]] | [(3840, 51840)] | 达到最长 3s / 5760 | К согласной ядерному управлению Японии на заводе. | ru / 0.946306 | К согласной ядерному управлению Японии на заводе. | 991.09 / 1.9062 / 341.17 | 7.707385918457511 |
| s002 | [[99840, 149760]] | [(51840, 101760)] | 静音结束/尾音下降 / 0 | и полябно ружина радиоактивной цези и йод. | ru / 0.989847 | и полябно ружина радиоактивной цези и йод. | 992.44 / 1.8750 / 342.20 | 8.233995488744341 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через комаров болезть затем передаяться

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": false, "transmission_relation_suspected": false, "disease_word_suspected": true, "human_recipient_suspected": false}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 983.59 / 1.9531 / 343.68 | 0.0 |
| s004 | [[245760, 293760]] | [(50560, 98560)] | 达到最长 3s / 0 | от которых через комаров болезть затем передаяться | ru / 0.901237 | от которых через комаров болезть затем передаяться | 990.80 / 1.9844 / 343.97 | 0.0 |
| s005 | [[293760, 307200]] | [(98560, 112000)] | 静音结束/尾音下降 / 0 |  | N/A | asr_budget_weak_drop | not submitted | N/A |

## r2-tick5-max4.5

Replay CPU 8.9688s; peak sampled RSS 344.07 MiB; drain=True; worker stopped=True.

### fleurs-ru-test-1692-10024935581249406669

Reference: Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.

Translation boundary (zero requests): Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные.

Automatic suspicion flags: `{"raw": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "retained": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "translation_input": {"radioactivity": true, "cesium_suspected": false, "iodine_suspected": false}, "non_russian_detected": ["nl"], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s001 | [[51840, 124800]] | [(3840, 76800)] | 达到最长 4.5s / 5760 | Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные. | ru / 0.961456 | Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные. | 1015.73 / 2.0156 / 337.08 | 7.29591354084414 |
| s002 | [[124800, 149760]] | [(76800, 101760)] | 静音结束/尾音下降 / 0 | het seise ijoud. | nl / 0.191841 | 语言置信度 0.19 < 0.35 | 961.76 / 2.0312 / 342.54 | 10.88482644748838 |

### fleurs-ru-holdout-1762-10098401296465388159

Reference: Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.

Translation boundary (zero requests): Переносчиками является свиньи. от которых через Комаров болезть затем передается человеку.

Automatic suspicion flags: `{"raw": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "retained": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "translation_input": {"pigs": true, "mosquito_word_suspected": true, "person_capitalization_suspected": true, "transmission_relation_suspected": true, "disease_word_suspected": true, "human_recipient_suspected": true}, "non_russian_detected": [], "semantic_correctness": "pending_bilingual_review", "word_timestamps": "missing; inspect segment WAVs; no inferred word boundaries"}`

Human verdict: **pending**. The lexical matcher is not semantic acceptance; e.g. separated `радио активной` can be a false negative.

| Segment | Stream frames | WAV frames | Cut / preroll frames | Raw ASR | Language/probability | Filter / retained text | ASR ms / CPU s / peak RSS MiB | Gain dB |
|---|---|---|---|---|---|---|---|---|
| s003 | [[197760, 245760]] | [(2560, 50560)] | speech_reentry / 5760 | Переносчиками является свиньи. | ru / 0.928149 | Переносчиками является свиньи. | 972.87 / 1.9375 / 343.15 | 0.0 |
| s004 | [[245760, 305280]] | [(50560, 110080)] | 静音结束/尾音下降 / 0 | от которых через Комаров болезть затем передается человеку. | ru / 0.960205 | от которых через Комаров болезть затем передается человеку. | 1008.50 / 1.9375 / 344.07 | 0.0 |
