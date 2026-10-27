---
annotations_creators:
- expert-generated
- crowdsourced
- machine-generated
language_creators:
- crowdsourced
- expert-generated
language:
- afr
- amh
- ara
- asm
- ast
- azj
- bel
- ben
- bos
- cat
- ceb
- cmn
- ces
- cym
- dan
- deu
- ell
- eng
- spa
- est
- fas
- ful
- fin
- tgl
- fra
- gle
- glg
- guj
- hau
- heb
- hin
- hrv
- hun
- hye
- ind
- ibo
- isl
- ita
- jpn
- jav
- kat
- kam
- kea
- kaz
- khm
- kan
- kor
- ckb
- kir
- ltz
- lug
- lin
- lao
- lit
- luo
- lav
- mri
- mkd
- mal
- mon
- mar
- msa
- mlt
- mya
- nob
- npi
- nld
- nso
- nya
- oci
- orm
- ory
- pan
- pol
- pus
- por
- ron
- rus
- bul
- snd
- slk
- slv
- sna
- som
- srp
- swe
- swh
- tam
- tel
- tgk
- tha
- tur
- ukr
- umb
- urd
- uzb
- vie
- wol
- xho
- yor
- yue
- zul
license:
- cc-by-4.0
multilinguality:
- multilingual
size_categories:
- 10K<n<100K
task_categories:
- automatic-speech-recognition
task_ids: []
pretty_name: 'The Cross-lingual TRansfer Evaluation of Multilingual Encoders for Speech
  (XTREME-S) benchmark is a benchmark designed to evaluate speech representations
  across languages, tasks, domains and data regimes. It covers 102 languages from
  10+ language families, 3 different domains and 4 task families: speech recognition,
  translation, classification and retrieval.'
tags:
- speech-recognition
dataset_info:
- config_name: af_za
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 839793847.872
    num_examples: 1032
  - name: validation
    num_bytes: 147329519.0
    num_examples: 198
  - name: test
    num_bytes: 207322551.0
    num_examples: 264
  download_size: 1174806083
  dataset_size: 1194445917.872
- config_name: all
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 227082369266.558
    num_examples: 271798
  - name: validation
    num_bytes: 27455873540.204
    num_examples: 34452
  - name: test
    num_bytes: 65209589116.9
    num_examples: 77810
  download_size: 315251122489
  dataset_size: 319747831923.66205
- config_name: am_et
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2559987829.952
    num_examples: 3163
  - name: validation
    num_bytes: 150599515.0
    num_examples: 223
  - name: test
    num_bytes: 371918215.0
    num_examples: 516
  download_size: 3053246300
  dataset_size: 3082505559.952
- config_name: ar_eg
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1395145023.816
    num_examples: 2104
  - name: validation
    num_bytes: 201650266.0
    num_examples: 295
  - name: test
    num_bytes: 300148405.0
    num_examples: 428
  download_size: 1878608285
  dataset_size: 1896943694.816
- config_name: as_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2465583287.124
    num_examples: 2812
  - name: validation
    num_bytes: 324811741.0
    num_examples: 418
  - name: test
    num_bytes: 800387791.0
    num_examples: 984
  download_size: 3569099001
  dataset_size: 3590782819.124
- config_name: ast_es
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1737884260.853
    num_examples: 2511
  - name: validation
    num_bytes: 227624292.0
    num_examples: 398
  - name: test
    num_bytes: 561873647.0
    num_examples: 946
  download_size: 2513631796
  dataset_size: 2527382199.8529997
- config_name: az_az
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2147472542.165
    num_examples: 2665
  - name: validation
    num_bytes: 311153963.0
    num_examples: 400
  - name: test
    num_bytes: 746469413.0
    num_examples: 923
  download_size: 3175632786
  dataset_size: 3205095918.165
- config_name: be_by
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2194326569.362
    num_examples: 2433
  - name: validation
    num_bytes: 380287144.0
    num_examples: 408
  - name: test
    num_bytes: 929886358.0
    num_examples: 967
  download_size: 3454952317
  dataset_size: 3504500071.362
- config_name: bg_bg
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2191856526.76
    num_examples: 2973
  - name: validation
    num_bytes: 243642176.0
    num_examples: 395
  - name: test
    num_bytes: 428458023.0
    num_examples: 658
  download_size: 2826925320
  dataset_size: 2863956725.76
- config_name: bn_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2474131730.702
    num_examples: 3006
  - name: validation
    num_bytes: 334077582.0
    num_examples: 402
  - name: test
    num_bytes: 791911631.0
    num_examples: 920
  download_size: 3591657059
  dataset_size: 3600120943.702
- config_name: bs_ba
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2303658222.648
    num_examples: 3091
  - name: validation
    num_bytes: 308416969.0
    num_examples: 400
  - name: test
    num_bytes: 729407573.0
    num_examples: 925
  download_size: 3272099984
  dataset_size: 3341482764.648
- config_name: ca_es
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1711896704.9
    num_examples: 2300
  - name: validation
    num_bytes: 298875429.0
    num_examples: 404
  - name: test
    num_bytes: 722929476.0
    num_examples: 940
  download_size: 2686093960
  dataset_size: 2733701609.9
- config_name: ceb_ph
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2806683031.405
    num_examples: 3261
  - name: validation
    num_bytes: 202682713.0
    num_examples: 225
  - name: test
    num_bytes: 510791213.0
    num_examples: 541
  download_size: 3488424502
  dataset_size: 3520156957.405
- config_name: ckb_iq
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2411115318.08
    num_examples: 3040
  - name: validation
    num_bytes: 284397470.0
    num_examples: 386
  - name: test
    num_bytes: 690450954.0
    num_examples: 922
  download_size: 3303138545
  dataset_size: 3385963742.08
- config_name: cmn_hans_cn
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2242562721.766
    num_examples: 3246
  - name: validation
    num_bytes: 293076201.0
    num_examples: 409
  - name: test
    num_bytes: 708671763.0
    num_examples: 945
  download_size: 3197922852
  dataset_size: 3244310685.766
- config_name: cs_cz
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1946665036.753
    num_examples: 2811
  - name: validation
    num_bytes: 228571616.0
    num_examples: 305
  - name: test
    num_bytes: 564854654.0
    num_examples: 723
  download_size: 2685388927
  dataset_size: 2740091306.7530003
- config_name: cy_gb
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2805819243.138
    num_examples: 3427
  - name: validation
    num_bytes: 415714120.0
    num_examples: 447
  - name: test
    num_bytes: 987523803.999
    num_examples: 1021
  download_size: 4138642374
  dataset_size: 4209057167.137
- config_name: da_dk
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1730329004.405
    num_examples: 2465
  - name: validation
    num_bytes: 270089990.0
    num_examples: 395
  - name: test
    num_bytes: 677558320.0
    num_examples: 930
  download_size: 2621082392
  dataset_size: 2677977314.4049997
- config_name: de_de
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2075399051.544
    num_examples: 2987
  - name: validation
    num_bytes: 291227170.0
    num_examples: 363
  - name: test
    num_bytes: 726840656.0
    num_examples: 862
  download_size: 3059767562
  dataset_size: 3093466877.5439997
- config_name: el_gr
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2316398281.435
    num_examples: 3215
  - name: validation
    num_bytes: 176874866.0
    num_examples: 271
  - name: test
    num_bytes: 439693449.0
    num_examples: 650
  download_size: 2905037120
  dataset_size: 2932966596.435
- config_name: en_us
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1727206652.832
    num_examples: 2602
  - name: validation
    num_bytes: 241171602.0
    num_examples: 394
  - name: test
    num_bytes: 409163240.0
    num_examples: 647
  download_size: 2359774185
  dataset_size: 2377541494.832
- config_name: es_419
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2030358518.54
    num_examples: 2796
  - name: validation
    num_bytes: 312009553.0
    num_examples: 408
  - name: test
    num_bytes: 712587610.0
    num_examples: 908
  download_size: 2857166127
  dataset_size: 3054955681.54
- config_name: et_ee
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1682672702.603
    num_examples: 2501
  - name: validation
    num_bytes: 286352938.0
    num_examples: 387
  - name: test
    num_bytes: 693292069.0
    num_examples: 893
  download_size: 2623632617
  dataset_size: 2662317709.6029997
- config_name: fa_ir
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2783059289.797
    num_examples: 3101
  - name: validation
    num_bytes: 352267036.0
    num_examples: 369
  - name: test
    num_bytes: 853202771.0
    num_examples: 871
  download_size: 3932337039
  dataset_size: 3988529096.797
- config_name: ff_sn
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3201254126.205
    num_examples: 3235
  - name: validation
    num_bytes: 238263811.0
    num_examples: 273
  - name: test
    num_bytes: 605602236.0
    num_examples: 660
  download_size: 4024954898
  dataset_size: 4045120173.205
- config_name: fi_fi
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2031612300.704
    num_examples: 2704
  - name: validation
    num_bytes: 325717756.0
    num_examples: 415
  - name: test
    num_bytes: 761741814.0
    num_examples: 918
  download_size: 3052477385
  dataset_size: 3119071870.704
- config_name: fil_ph
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1777223669.616
    num_examples: 1884
  - name: validation
    num_bytes: 455497736.0
    num_examples: 418
  - name: test
    num_bytes: 1104127010.0
    num_examples: 964
  download_size: 3314825178
  dataset_size: 3336848415.616
- config_name: fr_fr
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2380203654.546
    num_examples: 3193
  - name: validation
    num_bytes: 183377432.0
    num_examples: 289
  - name: test
    num_bytes: 449931787.0
    num_examples: 676
  download_size: 2942782406
  dataset_size: 3013512873.546
- config_name: ga_ie
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2793988266.275
    num_examples: 2845
  - name: validation
    num_bytes: 342626076.0
    num_examples: 369
  - name: test
    num_bytes: 798054644.0
    num_examples: 842
  download_size: 3870242970
  dataset_size: 3934668986.275
- config_name: gl_es
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1541154500.65
    num_examples: 2175
  - name: validation
    num_bytes: 241507716.0
    num_examples: 395
  - name: test
    num_bytes: 600568343.0
    num_examples: 927
  download_size: 2373476882
  dataset_size: 2383230559.65
- config_name: gu_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2069066254.515
    num_examples: 3145
  - name: validation
    num_bytes: 275449331.0
    num_examples: 432
  - name: test
    num_bytes: 672504271.0
    num_examples: 1000
  download_size: 3014392002
  dataset_size: 3017019856.5150003
- config_name: ha_ng
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3139325109.382
    num_examples: 3259
  - name: validation
    num_bytes: 352576137.0
    num_examples: 296
  - name: test
    num_bytes: 769867833.0
    num_examples: 621
  download_size: 4260173003
  dataset_size: 4261769079.382
- config_name: he_il
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2185005905.798
    num_examples: 3242
  - name: validation
    num_bytes: 189077577.0
    num_examples: 328
  - name: test
    num_bytes: 472969432.0
    num_examples: 792
  download_size: 2838882335
  dataset_size: 2847052914.798
- config_name: hi_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1535357348.2
    num_examples: 2120
  - name: validation
    num_bytes: 164370628.0
    num_examples: 239
  - name: test
    num_bytes: 309638443.0
    num_examples: 418
  download_size: 1997439747
  dataset_size: 2009366419.2
- config_name: hr_hr
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2715175044.32
    num_examples: 3461
  - name: validation
    num_bytes: 236182670.0
    num_examples: 377
  - name: test
    num_bytes: 591672296.0
    num_examples: 914
  download_size: 3441020498
  dataset_size: 3543030010.32
- config_name: hu_hu
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2141288381.83
    num_examples: 3095
  - name: validation
    num_bytes: 308087235.0
    num_examples: 407
  - name: test
    num_bytes: 707759295.0
    num_examples: 905
  download_size: 3126363016
  dataset_size: 3157134911.83
- config_name: hy_am
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2391276390.724
    num_examples: 3053
  - name: validation
    num_bytes: 278620946.0
    num_examples: 395
  - name: test
    num_bytes: 693427899.0
    num_examples: 932
  download_size: 3285288102
  dataset_size: 3363325235.724
- config_name: id_id
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2096527229.426
    num_examples: 2579
  - name: validation
    num_bytes: 267264141.0
    num_examples: 350
  - name: test
    num_bytes: 545358212.0
    num_examples: 687
  download_size: 2897281998
  dataset_size: 2909149582.426
- config_name: ig_ng
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3179642803.934
    num_examples: 2839
  - name: validation
    num_bytes: 437483894.0
    num_examples: 413
  - name: test
    num_bytes: 1109139543.0
    num_examples: 969
  download_size: 4581028394
  dataset_size: 4726266240.934
- config_name: is_is
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 656533354.0
    num_examples: 926
  - name: validation
    num_bytes: 27705374.0
    num_examples: 36
  - name: test
    num_bytes: 41298808.0
    num_examples: 46
  download_size: 720265634
  dataset_size: 725537536.0
- config_name: it_it
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2074837404.42
    num_examples: 3030
  - name: validation
    num_bytes: 356573617.0
    num_examples: 391
  - name: test
    num_bytes: 811767121.0
    num_examples: 865
  download_size: 3196701958
  dataset_size: 3243178142.42
- config_name: ja_jp
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1710594415.996
    num_examples: 2292
  - name: validation
    num_bytes: 217077093.0
    num_examples: 266
  - name: test
    num_bytes: 545080936.0
    num_examples: 650
  download_size: 2443785992
  dataset_size: 2472752444.9960003
- config_name: jv_id
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2580147331.712
    num_examples: 3051
  - name: validation
    num_bytes: 256538338.0
    num_examples: 295
  - name: test
    num_bytes: 648426252.0
    num_examples: 728
  download_size: 3481250544
  dataset_size: 3485111921.712
- config_name: ka_ge
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1168919302.616
    num_examples: 1491
  - name: validation
    num_bytes: 281493288.0
    num_examples: 409
  - name: test
    num_bytes: 708435695.0
    num_examples: 979
  download_size: 2135126815
  dataset_size: 2158848285.616
- config_name: kam_ke
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3399703514.2
    num_examples: 3340
  - name: validation
    num_bytes: 333156556.0
    num_examples: 338
  - name: test
    num_bytes: 859832194.0
    num_examples: 827
  download_size: 4582071678
  dataset_size: 4592692264.2
- config_name: kea_cv
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2422585691.075
    num_examples: 2715
  - name: validation
    num_bytes: 305116842.0
    num_examples: 366
  - name: test
    num_bytes: 753137632.0
    num_examples: 864
  download_size: 3458147336
  dataset_size: 3480840165.075
- config_name: kk_kz
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2720172301.8
    num_examples: 3200
  - name: validation
    num_bytes: 351930053.0
    num_examples: 369
  - name: test
    num_bytes: 884117916.0
    num_examples: 856
  download_size: 3861486625
  dataset_size: 3956220270.8
- config_name: km_kh
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1637932993.85
    num_examples: 1675
  - name: validation
    num_bytes: 297472890.0
    num_examples: 326
  - name: test
    num_bytes: 726811243.0
    num_examples: 771
  download_size: 2611296692
  dataset_size: 2662217126.85
- config_name: kn_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1910007372.243
    num_examples: 2283
  - name: validation
    num_bytes: 299911900.0
    num_examples: 368
  - name: test
    num_bytes: 732867277.0
    num_examples: 838
  download_size: 2914549831
  dataset_size: 2942786549.243
- config_name: ko_kr
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1829042683.788
    num_examples: 2307
  - name: validation
    num_bytes: 178036846.0
    num_examples: 226
  - name: test
    num_bytes: 307727990.0
    num_examples: 382
  download_size: 2276191421
  dataset_size: 2314807519.788
- config_name: ky_kg
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2150729093.8
    num_examples: 2818
  - name: validation
    num_bytes: 307920627.0
    num_examples: 422
  - name: test
    num_bytes: 748673876.0
    num_examples: 977
  download_size: 3140279335
  dataset_size: 3207323596.8
- config_name: lb_lu
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1950382298.24
    num_examples: 2502
  - name: validation
    num_bytes: 257325971.0
    num_examples: 408
  - name: test
    num_bytes: 629871690.0
    num_examples: 934
  download_size: 2740795823
  dataset_size: 2837579959.24
- config_name: lg_ug
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2912375679.492
    num_examples: 2478
  - name: validation
    num_bytes: 321131987.0
    num_examples: 306
  - name: test
    num_bytes: 784357340.0
    num_examples: 723
  download_size: 3957713711
  dataset_size: 4017865006.492
- config_name: ln_cd
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 4203557689.55
    num_examples: 3350
  - name: validation
    num_bytes: 245582053.0
    num_examples: 209
  - name: test
    num_bytes: 595588765.0
    num_examples: 478
  download_size: 5030451722
  dataset_size: 5044728507.55
- config_name: lo_la
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1694576407.811
    num_examples: 1809
  - name: validation
    num_bytes: 132582508.0
    num_examples: 191
  - name: test
    num_bytes: 324413436.0
    num_examples: 405
  download_size: 2150301883
  dataset_size: 2151572351.811
- config_name: lt_lt
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2248503610.566
    num_examples: 2937
  - name: validation
    num_bytes: 270114040.0
    num_examples: 416
  - name: test
    num_bytes: 684468529.0
    num_examples: 986
  download_size: 3130440333
  dataset_size: 3203086179.566
- config_name: luo_ke
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2333433934.544
    num_examples: 2384
  - name: validation
    num_bytes: 85864373.0
    num_examples: 102
  - name: test
    num_bytes: 224619173.0
    num_examples: 256
  download_size: 2552501079
  dataset_size: 2643917480.544
- config_name: lv_lv
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1505531921.76
    num_examples: 2110
  - name: validation
    num_bytes: 259171539.0
    num_examples: 356
  - name: test
    num_bytes: 654449736.0
    num_examples: 851
  download_size: 2365577223
  dataset_size: 2419153196.76
- config_name: mi_nz
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 4189456682.9
    num_examples: 3249
  - name: validation
    num_bytes: 533706368.0
    num_examples: 429
  - name: test
    num_bytes: 1346889828.768
    num_examples: 1008
  download_size: 6040701291
  dataset_size: 6070052879.667999
- config_name: mk_mk
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1569948025.385
    num_examples: 2337
  - name: validation
    num_bytes: 296967136.0
    num_examples: 415
  - name: test
    num_bytes: 738828967.0
    num_examples: 973
  download_size: 2580288599
  dataset_size: 2605744128.385
- config_name: ml_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2319861048.945
    num_examples: 3043
  - name: validation
    num_bytes: 387743554.0
    num_examples: 418
  - name: test
    num_bytes: 901670151.0
    num_examples: 958
  download_size: 3587756904
  dataset_size: 3609274753.945
- config_name: mn_mn
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2264251001.362
    num_examples: 3074
  - name: validation
    num_bytes: 268960699.0
    num_examples: 405
  - name: test
    num_bytes: 657800430.0
    num_examples: 949
  download_size: 3102508053
  dataset_size: 3191012130.362
- config_name: mr_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2756016324.204
    num_examples: 3269
  - name: validation
    num_bytes: 360231388.0
    num_examples: 443
  - name: test
    num_bytes: 889513780.33
    num_examples: 1015
  download_size: 3978946143
  dataset_size: 4005761492.534
- config_name: ms_my
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2201722924.038
    num_examples: 2667
  - name: validation
    num_bytes: 213319709.0
    num_examples: 324
  - name: test
    num_bytes: 522026472.0
    num_examples: 749
  download_size: 2919753704
  dataset_size: 2937069105.038
- config_name: mt_mt
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2284625076.61
    num_examples: 2895
  - name: validation
    num_bytes: 344453173.0
    num_examples: 404
  - name: test
    num_bytes: 817836084.0
    num_examples: 926
  download_size: 3393423239
  dataset_size: 3446914333.61
- config_name: my_mm
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2799418051.83
    num_examples: 3058
  - name: validation
    num_bytes: 378951004.0
    num_examples: 384
  - name: test
    num_bytes: 879854221.0
    num_examples: 880
  download_size: 3937715423
  dataset_size: 4058223276.83
- config_name: nb_no
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2515922330.207
    num_examples: 3167
  - name: validation
    num_bytes: 132919125.0
    num_examples: 163
  - name: test
    num_bytes: 287480481.0
    num_examples: 357
  download_size: 2915731512
  dataset_size: 2936321936.207
- config_name: ne_np
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2610816162.86
    num_examples: 3332
  - name: validation
    num_bytes: 209207514.0
    num_examples: 305
  - name: test
    num_bytes: 527009850.0
    num_examples: 726
  download_size: 3301167451
  dataset_size: 3347033526.86
- config_name: nl_nl
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1766642965.308
    num_examples: 2918
  - name: validation
    num_bytes: 104005626.0
    num_examples: 171
  - name: test
    num_bytes: 223391943.0
    num_examples: 364
  download_size: 2079775236
  dataset_size: 2094040534.308
- config_name: nso_za
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3021393004.9
    num_examples: 1990
  - name: validation
    num_bytes: 421513918.0
    num_examples: 363
  - name: test
    num_bytes: 968657264.0
    num_examples: 790
  download_size: 4378157804
  dataset_size: 4411564186.9
- config_name: ny_mw
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2506497222.378
    num_examples: 2694
  - name: validation
    num_bytes: 316040445.0
    num_examples: 311
  - name: test
    num_bytes: 810668835.0
    num_examples: 761
  download_size: 3617116335
  dataset_size: 3633206502.378
- config_name: oc_fr
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3289020327.594
    num_examples: 3379
  - name: validation
    num_bytes: 416315648.0
    num_examples: 427
  - name: test
    num_bytes: 1039370490.0
    num_examples: 998
  download_size: 4634297460
  dataset_size: 4744706465.594
- config_name: om_et
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1534479800.828
    num_examples: 1701
  - name: validation
    num_bytes: 13814098.0
    num_examples: 19
  - name: test
    num_bytes: 29968213.0
    num_examples: 41
  download_size: 1569558999
  dataset_size: 1578262111.828
- config_name: or_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 792407998.441
    num_examples: 1081
  - name: validation
    num_bytes: 286388715.0
    num_examples: 392
  - name: test
    num_bytes: 684047545.0
    num_examples: 883
  download_size: 1744141795
  dataset_size: 1762844258.441
- config_name: pa_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1467446401.375
    num_examples: 1923
  - name: validation
    num_bytes: 172374668.0
    num_examples: 251
  - name: test
    num_bytes: 423657651.0
    num_examples: 574
  download_size: 2045982318
  dataset_size: 2063478720.375
- config_name: pl_pl
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2116561345.941
    num_examples: 2841
  - name: validation
    num_bytes: 194818355.0
    num_examples: 338
  - name: test
    num_bytes: 472887992.0
    num_examples: 758
  download_size: 2736483246
  dataset_size: 2784267692.941
- config_name: ps_af
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2048577629.761
    num_examples: 2513
  - name: validation
    num_bytes: 165817187.0
    num_examples: 217
  - name: test
    num_bytes: 406726295.0
    num_examples: 512
  download_size: 2581342956
  dataset_size: 2621121111.7609997
- config_name: pt_br
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2346702832.609
    num_examples: 2793
  - name: validation
    num_bytes: 297649021.0
    num_examples: 386
  - name: test
    num_bytes: 746751650.0
    num_examples: 919
  download_size: 3355359116
  dataset_size: 3391103503.609
- config_name: ro_ro
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2334084639.408
    num_examples: 2891
  - name: validation
    num_bytes: 248481792.0
    num_examples: 387
  - name: test
    num_bytes: 582858099.0
    num_examples: 883
  download_size: 3148472658
  dataset_size: 3165424530.408
- config_name: ru_ru
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1856730279.324
    num_examples: 2562
  - name: validation
    num_bytes: 248810162.0
    num_examples: 356
  - name: test
    num_bytes: 576202027.0
    num_examples: 775
  download_size: 2636505060
  dataset_size: 2681742468.324
- config_name: sd_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2832065181.515
    num_examples: 3443
  - name: validation
    num_bytes: 306643766.0
    num_examples: 426
  - name: test
    num_bytes: 759190196.0
    num_examples: 980
  download_size: 3894654954
  dataset_size: 3897899143.515
- config_name: sk_sk
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1352992761.894
    num_examples: 1957
  - name: validation
    num_bytes: 250783343.0
    num_examples: 352
  - name: test
    num_bytes: 602582911.0
    num_examples: 792
  download_size: 2162629863
  dataset_size: 2206359015.894
- config_name: sl_si
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1790258499.688
    num_examples: 2512
  - name: validation
    num_bytes: 206108127.0
    num_examples: 349
  - name: test
    num_bytes: 523514416.0
    num_examples: 834
  download_size: 2469850018
  dataset_size: 2519881042.6879997
- config_name: sn_zw
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2300402255.782
    num_examples: 2463
  - name: validation
    num_bytes: 356304386.0
    num_examples: 393
  - name: test
    num_bytes: 880211193.0
    num_examples: 925
  download_size: 3459145133
  dataset_size: 3536917834.782
- config_name: so_so
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3069997235.986
    num_examples: 3149
  - name: validation
    num_bytes: 357302560.0
    num_examples: 432
  - name: test
    num_bytes: 902709809.609
    num_examples: 1019
  download_size: 4252574748
  dataset_size: 4330009605.595
- config_name: sr_rs
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2458039803.624
    num_examples: 2944
  - name: validation
    num_bytes: 192352546.0
    num_examples: 290
  - name: test
    num_bytes: 490001586.0
    num_examples: 700
  download_size: 3125217698
  dataset_size: 3140393935.624
- config_name: sv_se
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1927558847.58
    num_examples: 2385
  - name: validation
    num_bytes: 227049010.0
    num_examples: 330
  - name: test
    num_bytes: 537947269.0
    num_examples: 759
  download_size: 2571785762
  dataset_size: 2692555126.58
- config_name: sw_ke
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3105325843.47
    num_examples: 3070
  - name: validation
    num_bytes: 184816031.0
    num_examples: 211
  - name: test
    num_bytes: 444376732.0
    num_examples: 487
  download_size: 3716576769
  dataset_size: 3734518606.47
- config_name: ta_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2001978625.636
    num_examples: 2367
  - name: validation
    num_bytes: 289493909.0
    num_examples: 377
  - name: test
    num_bytes: 491668412.0
    num_examples: 591
  download_size: 2764762962
  dataset_size: 2783140946.6359997
- config_name: te_in
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1826020734.522
    num_examples: 2302
  - name: validation
    num_bytes: 206277104.0
    num_examples: 311
  - name: test
    num_bytes: 334280072.0
    num_examples: 472
  download_size: 2344140373
  dataset_size: 2366577910.5220003
- config_name: tg_tj
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1983043746.164
    num_examples: 2298
  - name: validation
    num_bytes: 218600543.0
    num_examples: 240
  - name: test
    num_bytes: 558603653.0
    num_examples: 600
  download_size: 2691321614
  dataset_size: 2760247942.164
- config_name: th_th
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1958751720.2
    num_examples: 2602
  - name: validation
    num_bytes: 329357865.0
    num_examples: 439
  - name: test
    num_bytes: 789384153.138
    num_examples: 1021
  download_size: 3064431406
  dataset_size: 3077493738.338
- config_name: tr_tr
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1913682419.438
    num_examples: 2526
  - name: validation
    num_bytes: 258352632.0
    num_examples: 338
  - name: test
    num_bytes: 600739184.0
    num_examples: 743
  download_size: 2738599502
  dataset_size: 2772774235.4379997
- config_name: uk_ua
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2083680961.06
    num_examples: 2810
  - name: validation
    num_bytes: 217245702.0
    num_examples: 325
  - name: test
    num_bytes: 521842841.0
    num_examples: 750
  download_size: 2769906439
  dataset_size: 2822769504.06
- config_name: umb_ao
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2605372014.503
    num_examples: 1597
  - name: validation
    num_bytes: 218495880.0
    num_examples: 135
  - name: test
    num_bytes: 632771041.0
    num_examples: 379
  download_size: 3431316900
  dataset_size: 3456638935.503
- config_name: ur_pk
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1620807072.862
    num_examples: 2109
  - name: validation
    num_bytes: 174193615.0
    num_examples: 267
  - name: test
    num_bytes: 187857715.0
    num_examples: 299
  download_size: 1959959518
  dataset_size: 1982858402.862
- config_name: uz_uz
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2324391443.761
    num_examples: 2943
  - name: validation
    num_bytes: 268314272.0
    num_examples: 363
  - name: test
    num_bytes: 654226718.0
    num_examples: 862
  download_size: 3188045168
  dataset_size: 3246932433.761
- config_name: vi_vn
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2093031792.394
    num_examples: 2994
  - name: validation
    num_bytes: 275388624.0
    num_examples: 361
  - name: test
    num_bytes: 692607848.0
    num_examples: 857
  download_size: 3038985670
  dataset_size: 3061028264.394
- config_name: wo_sn
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2010988151.295
    num_examples: 2279
  - name: validation
    num_bytes: 176896848.0
    num_examples: 169
  - name: test
    num_bytes: 402770325.0
    num_examples: 371
  download_size: 2392054344
  dataset_size: 2590655324.295
- config_name: xh_za
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3074255674.192
    num_examples: 3466
  - name: validation
    num_bytes: 355301580.0
    num_examples: 446
  - name: test
    num_bytes: 872018986.944
    num_examples: 1041
  download_size: 4209570267
  dataset_size: 4301576241.136
- config_name: yo_ng
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 2312709259.205
    num_examples: 2339
  - name: validation
    num_bytes: 394971927.0
    num_examples: 378
  - name: test
    num_bytes: 868268539.0
    num_examples: 831
  download_size: 3573399742
  dataset_size: 3575949725.205
- config_name: yue_hant_hk
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 1674023661.887
    num_examples: 1939
  - name: validation
    num_bytes: 263125012.0
    num_examples: 362
  - name: test
    num_bytes: 610944753.0
    num_examples: 819
  download_size: 2541552925
  dataset_size: 2548093426.887
- config_name: zu_za
  features:
  - name: id
    dtype: int32
  - name: num_samples
    dtype: int32
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 16000
  - name: transcription
    dtype: string
  - name: raw_transcription
    dtype: string
  - name: gender
    dtype:
      class_label:
        names:
          '0': male
          '1': female
          '2': other
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': af_za
          '1': am_et
          '2': ar_eg
          '3': as_in
          '4': ast_es
          '5': az_az
          '6': be_by
          '7': bg_bg
          '8': bn_in
          '9': bs_ba
          '10': ca_es
          '11': ceb_ph
          '12': ckb_iq
          '13': cmn_hans_cn
          '14': cs_cz
          '15': cy_gb
          '16': da_dk
          '17': de_de
          '18': el_gr
          '19': en_us
          '20': es_419
          '21': et_ee
          '22': fa_ir
          '23': ff_sn
          '24': fi_fi
          '25': fil_ph
          '26': fr_fr
          '27': ga_ie
          '28': gl_es
          '29': gu_in
          '30': ha_ng
          '31': he_il
          '32': hi_in
          '33': hr_hr
          '34': hu_hu
          '35': hy_am
          '36': id_id
          '37': ig_ng
          '38': is_is
          '39': it_it
          '40': ja_jp
          '41': jv_id
          '42': ka_ge
          '43': kam_ke
          '44': kea_cv
          '45': kk_kz
          '46': km_kh
          '47': kn_in
          '48': ko_kr
          '49': ky_kg
          '50': lb_lu
          '51': lg_ug
          '52': ln_cd
          '53': lo_la
          '54': lt_lt
          '55': luo_ke
          '56': lv_lv
          '57': mi_nz
          '58': mk_mk
          '59': ml_in
          '60': mn_mn
          '61': mr_in
          '62': ms_my
          '63': mt_mt
          '64': my_mm
          '65': nb_no
          '66': ne_np
          '67': nl_nl
          '68': nso_za
          '69': ny_mw
          '70': oc_fr
          '71': om_et
          '72': or_in
          '73': pa_in
          '74': pl_pl
          '75': ps_af
          '76': pt_br
          '77': ro_ro
          '78': ru_ru
          '79': sd_in
          '80': sk_sk
          '81': sl_si
          '82': sn_zw
          '83': so_so
          '84': sr_rs
          '85': sv_se
          '86': sw_ke
          '87': ta_in
          '88': te_in
          '89': tg_tj
          '90': th_th
          '91': tr_tr
          '92': uk_ua
          '93': umb_ao
          '94': ur_pk
          '95': uz_uz
          '96': vi_vn
          '97': wo_sn
          '98': xh_za
          '99': yo_ng
          '100': yue_hant_hk
          '101': zu_za
          '102': all
  - name: language
    dtype: string
  - name: lang_group_id
    dtype:
      class_label:
        names:
          '0': western_european_we
          '1': eastern_european_ee
          '2': central_asia_middle_north_african_cmn
          '3': sub_saharan_african_ssa
          '4': south_asian_sa
          '5': south_east_asian_sea
          '6': chinese_japanase_korean_cjk
  splits:
  - name: train
    num_bytes: 3302600339.658
    num_examples: 2858
  - name: validation
    num_bytes: 352298885.0
    num_examples: 354
  - name: test
    num_bytes: 893328809.0
    num_examples: 854
  download_size: 4464530306
  dataset_size: 4548228033.658
configs:
- config_name: af_za
  data_files:
  - split: train
    path: parquet-data/af_za/train-*
  - split: validation
    path: parquet-data/af_za/validation-*
  - split: test
    path: parquet-data/af_za/test-*
- config_name: all
  data_files:
  - split: train
    path: parquet-data/all/train-*
  - split: validation
    path: parquet-data/all/validation-*
  - split: test
    path: parquet-data/all/test-*
- config_name: am_et
  data_files:
  - split: train
    path: parquet-data/am_et/train-*
  - split: validation
    path: parquet-data/am_et/validation-*
  - split: test
    path: parquet-data/am_et/test-*
- config_name: ar_eg
  data_files:
  - split: train
    path: parquet-data/ar_eg/train-*
  - split: validation
    path: parquet-data/ar_eg/validation-*
  - split: test
    path: parquet-data/ar_eg/test-*
- config_name: as_in
  data_files:
  - split: train
    path: parquet-data/as_in/train-*
  - split: validation
    path: parquet-data/as_in/validation-*
  - split: test
    path: parquet-data/as_in/test-*
- config_name: ast_es
  data_files:
  - split: train
    path: parquet-data/ast_es/train-*
  - split: validation
    path: parquet-data/ast_es/validation-*
  - split: test
    path: parquet-data/ast_es/test-*
- config_name: az_az
  data_files:
  - split: train
    path: parquet-data/az_az/train-*
  - split: validation
    path: parquet-data/az_az/validation-*
  - split: test
    path: parquet-data/az_az/test-*
- config_name: be_by
  data_files:
  - split: train
    path: parquet-data/be_by/train-*
  - split: validation
    path: parquet-data/be_by/validation-*
  - split: test
    path: parquet-data/be_by/test-*
- config_name: bg_bg
  data_files:
  - split: train
    path: parquet-data/bg_bg/train-*
  - split: validation
    path: parquet-data/bg_bg/validation-*
  - split: test
    path: parquet-data/bg_bg/test-*
- config_name: bn_in
  data_files:
  - split: train
    path: parquet-data/bn_in/train-*
  - split: validation
    path: parquet-data/bn_in/validation-*
  - split: test
    path: parquet-data/bn_in/test-*
- config_name: bs_ba
  data_files:
  - split: train
    path: parquet-data/bs_ba/train-*
  - split: validation
    path: parquet-data/bs_ba/validation-*
  - split: test
    path: parquet-data/bs_ba/test-*
- config_name: ca_es
  data_files:
  - split: train
    path: parquet-data/ca_es/train-*
  - split: validation
    path: parquet-data/ca_es/validation-*
  - split: test
    path: parquet-data/ca_es/test-*
- config_name: ceb_ph
  data_files:
  - split: train
    path: parquet-data/ceb_ph/train-*
  - split: validation
    path: parquet-data/ceb_ph/validation-*
  - split: test
    path: parquet-data/ceb_ph/test-*
- config_name: ckb_iq
  data_files:
  - split: train
    path: parquet-data/ckb_iq/train-*
  - split: validation
    path: parquet-data/ckb_iq/validation-*
  - split: test
    path: parquet-data/ckb_iq/test-*
- config_name: cmn_hans_cn
  data_files:
  - split: train
    path: parquet-data/cmn_hans_cn/train-*
  - split: validation
    path: parquet-data/cmn_hans_cn/validation-*
  - split: test
    path: parquet-data/cmn_hans_cn/test-*
- config_name: cs_cz
  data_files:
  - split: train
    path: parquet-data/cs_cz/train-*
  - split: validation
    path: parquet-data/cs_cz/validation-*
  - split: test
    path: parquet-data/cs_cz/test-*
- config_name: cy_gb
  data_files:
  - split: train
    path: parquet-data/cy_gb/train-*
  - split: validation
    path: parquet-data/cy_gb/validation-*
  - split: test
    path: parquet-data/cy_gb/test-*
- config_name: da_dk
  data_files:
  - split: train
    path: parquet-data/da_dk/train-*
  - split: validation
    path: parquet-data/da_dk/validation-*
  - split: test
    path: parquet-data/da_dk/test-*
- config_name: de_de
  data_files:
  - split: train
    path: parquet-data/de_de/train-*
  - split: validation
    path: parquet-data/de_de/validation-*
  - split: test
    path: parquet-data/de_de/test-*
- config_name: el_gr
  data_files:
  - split: train
    path: parquet-data/el_gr/train-*
  - split: validation
    path: parquet-data/el_gr/validation-*
  - split: test
    path: parquet-data/el_gr/test-*
- config_name: en_us
  data_files:
  - split: train
    path: parquet-data/en_us/train-*
  - split: validation
    path: parquet-data/en_us/validation-*
  - split: test
    path: parquet-data/en_us/test-*
- config_name: es_419
  data_files:
  - split: train
    path: parquet-data/es_419/train-*
  - split: validation
    path: parquet-data/es_419/validation-*
  - split: test
    path: parquet-data/es_419/test-*
- config_name: et_ee
  data_files:
  - split: train
    path: parquet-data/et_ee/train-*
  - split: validation
    path: parquet-data/et_ee/validation-*
  - split: test
    path: parquet-data/et_ee/test-*
- config_name: fa_ir
  data_files:
  - split: train
    path: parquet-data/fa_ir/train-*
  - split: validation
    path: parquet-data/fa_ir/validation-*
  - split: test
    path: parquet-data/fa_ir/test-*
- config_name: ff_sn
  data_files:
  - split: train
    path: parquet-data/ff_sn/train-*
  - split: validation
    path: parquet-data/ff_sn/validation-*
  - split: test
    path: parquet-data/ff_sn/test-*
- config_name: fi_fi
  data_files:
  - split: train
    path: parquet-data/fi_fi/train-*
  - split: validation
    path: parquet-data/fi_fi/validation-*
  - split: test
    path: parquet-data/fi_fi/test-*
- config_name: fil_ph
  data_files:
  - split: train
    path: parquet-data/fil_ph/train-*
  - split: validation
    path: parquet-data/fil_ph/validation-*
  - split: test
    path: parquet-data/fil_ph/test-*
- config_name: fr_fr
  data_files:
  - split: train
    path: parquet-data/fr_fr/train-*
  - split: validation
    path: parquet-data/fr_fr/validation-*
  - split: test
    path: parquet-data/fr_fr/test-*
- config_name: ga_ie
  data_files:
  - split: train
    path: parquet-data/ga_ie/train-*
  - split: validation
    path: parquet-data/ga_ie/validation-*
  - split: test
    path: parquet-data/ga_ie/test-*
- config_name: gl_es
  data_files:
  - split: train
    path: parquet-data/gl_es/train-*
  - split: validation
    path: parquet-data/gl_es/validation-*
  - split: test
    path: parquet-data/gl_es/test-*
- config_name: gu_in
  data_files:
  - split: train
    path: parquet-data/gu_in/train-*
  - split: validation
    path: parquet-data/gu_in/validation-*
  - split: test
    path: parquet-data/gu_in/test-*
- config_name: ha_ng
  data_files:
  - split: train
    path: parquet-data/ha_ng/train-*
  - split: validation
    path: parquet-data/ha_ng/validation-*
  - split: test
    path: parquet-data/ha_ng/test-*
- config_name: he_il
  data_files:
  - split: train
    path: parquet-data/he_il/train-*
  - split: validation
    path: parquet-data/he_il/validation-*
  - split: test
    path: parquet-data/he_il/test-*
- config_name: hi_in
  data_files:
  - split: train
    path: parquet-data/hi_in/train-*
  - split: validation
    path: parquet-data/hi_in/validation-*
  - split: test
    path: parquet-data/hi_in/test-*
- config_name: hr_hr
  data_files:
  - split: train
    path: parquet-data/hr_hr/train-*
  - split: validation
    path: parquet-data/hr_hr/validation-*
  - split: test
    path: parquet-data/hr_hr/test-*
- config_name: hu_hu
  data_files:
  - split: train
    path: parquet-data/hu_hu/train-*
  - split: validation
    path: parquet-data/hu_hu/validation-*
  - split: test
    path: parquet-data/hu_hu/test-*
- config_name: hy_am
  data_files:
  - split: train
    path: parquet-data/hy_am/train-*
  - split: validation
    path: parquet-data/hy_am/validation-*
  - split: test
    path: parquet-data/hy_am/test-*
- config_name: id_id
  data_files:
  - split: train
    path: parquet-data/id_id/train-*
  - split: validation
    path: parquet-data/id_id/validation-*
  - split: test
    path: parquet-data/id_id/test-*
- config_name: ig_ng
  data_files:
  - split: train
    path: parquet-data/ig_ng/train-*
  - split: validation
    path: parquet-data/ig_ng/validation-*
  - split: test
    path: parquet-data/ig_ng/test-*
- config_name: is_is
  data_files:
  - split: train
    path: parquet-data/is_is/train-*
  - split: validation
    path: parquet-data/is_is/validation-*
  - split: test
    path: parquet-data/is_is/test-*
- config_name: it_it
  data_files:
  - split: train
    path: parquet-data/it_it/train-*
  - split: validation
    path: parquet-data/it_it/validation-*
  - split: test
    path: parquet-data/it_it/test-*
- config_name: ja_jp
  data_files:
  - split: train
    path: parquet-data/ja_jp/train-*
  - split: validation
    path: parquet-data/ja_jp/validation-*
  - split: test
    path: parquet-data/ja_jp/test-*
- config_name: jv_id
  data_files:
  - split: train
    path: parquet-data/jv_id/train-*
  - split: validation
    path: parquet-data/jv_id/validation-*
  - split: test
    path: parquet-data/jv_id/test-*
- config_name: ka_ge
  data_files:
  - split: train
    path: parquet-data/ka_ge/train-*
  - split: validation
    path: parquet-data/ka_ge/validation-*
  - split: test
    path: parquet-data/ka_ge/test-*
- config_name: kam_ke
  data_files:
  - split: train
    path: parquet-data/kam_ke/train-*
  - split: validation
    path: parquet-data/kam_ke/validation-*
  - split: test
    path: parquet-data/kam_ke/test-*
- config_name: kea_cv
  data_files:
  - split: train
    path: parquet-data/kea_cv/train-*
  - split: validation
    path: parquet-data/kea_cv/validation-*
  - split: test
    path: parquet-data/kea_cv/test-*
- config_name: kk_kz
  data_files:
  - split: train
    path: parquet-data/kk_kz/train-*
  - split: validation
    path: parquet-data/kk_kz/validation-*
  - split: test
    path: parquet-data/kk_kz/test-*
- config_name: km_kh
  data_files:
  - split: train
    path: parquet-data/km_kh/train-*
  - split: validation
    path: parquet-data/km_kh/validation-*
  - split: test
    path: parquet-data/km_kh/test-*
- config_name: kn_in
  data_files:
  - split: train
    path: parquet-data/kn_in/train-*
  - split: validation
    path: parquet-data/kn_in/validation-*
  - split: test
    path: parquet-data/kn_in/test-*
- config_name: ko_kr
  data_files:
  - split: train
    path: parquet-data/ko_kr/train-*
  - split: validation
    path: parquet-data/ko_kr/validation-*
  - split: test
    path: parquet-data/ko_kr/test-*
- config_name: ky_kg
  data_files:
  - split: train
    path: parquet-data/ky_kg/train-*
  - split: validation
    path: parquet-data/ky_kg/validation-*
  - split: test
    path: parquet-data/ky_kg/test-*
- config_name: lb_lu
  data_files:
  - split: train
    path: parquet-data/lb_lu/train-*
  - split: validation
    path: parquet-data/lb_lu/validation-*
  - split: test
    path: parquet-data/lb_lu/test-*
- config_name: lg_ug
  data_files:
  - split: train
    path: parquet-data/lg_ug/train-*
  - split: validation
    path: parquet-data/lg_ug/validation-*
  - split: test
    path: parquet-data/lg_ug/test-*
- config_name: ln_cd
  data_files:
  - split: train
    path: parquet-data/ln_cd/train-*
  - split: validation
    path: parquet-data/ln_cd/validation-*
  - split: test
    path: parquet-data/ln_cd/test-*
- config_name: lo_la
  data_files:
  - split: train
    path: parquet-data/lo_la/train-*
  - split: validation
    path: parquet-data/lo_la/validation-*
  - split: test
    path: parquet-data/lo_la/test-*
- config_name: lt_lt
  data_files:
  - split: train
    path: parquet-data/lt_lt/train-*
  - split: validation
    path: parquet-data/lt_lt/validation-*
  - split: test
    path: parquet-data/lt_lt/test-*
- config_name: luo_ke
  data_files:
  - split: train
    path: parquet-data/luo_ke/train-*
  - split: validation
    path: parquet-data/luo_ke/validation-*
  - split: test
    path: parquet-data/luo_ke/test-*
- config_name: lv_lv
  data_files:
  - split: train
    path: parquet-data/lv_lv/train-*
  - split: validation
    path: parquet-data/lv_lv/validation-*
  - split: test
    path: parquet-data/lv_lv/test-*
- config_name: mi_nz
  data_files:
  - split: train
    path: parquet-data/mi_nz/train-*
  - split: validation
    path: parquet-data/mi_nz/validation-*
  - split: test
    path: parquet-data/mi_nz/test-*
- config_name: mk_mk
  data_files:
  - split: train
    path: parquet-data/mk_mk/train-*
  - split: validation
    path: parquet-data/mk_mk/validation-*
  - split: test
    path: parquet-data/mk_mk/test-*
- config_name: ml_in
  data_files:
  - split: train
    path: parquet-data/ml_in/train-*
  - split: validation
    path: parquet-data/ml_in/validation-*
  - split: test
    path: parquet-data/ml_in/test-*
- config_name: mn_mn
  data_files:
  - split: train
    path: parquet-data/mn_mn/train-*
  - split: validation
    path: parquet-data/mn_mn/validation-*
  - split: test
    path: parquet-data/mn_mn/test-*
- config_name: mr_in
  data_files:
  - split: train
    path: parquet-data/mr_in/train-*
  - split: validation
    path: parquet-data/mr_in/validation-*
  - split: test
    path: parquet-data/mr_in/test-*
- config_name: ms_my
  data_files:
  - split: train
    path: parquet-data/ms_my/train-*
  - split: validation
    path: parquet-data/ms_my/validation-*
  - split: test
    path: parquet-data/ms_my/test-*
- config_name: mt_mt
  data_files:
  - split: train
    path: parquet-data/mt_mt/train-*
  - split: validation
    path: parquet-data/mt_mt/validation-*
  - split: test
    path: parquet-data/mt_mt/test-*
- config_name: my_mm
  data_files:
  - split: train
    path: parquet-data/my_mm/train-*
  - split: validation
    path: parquet-data/my_mm/validation-*
  - split: test
    path: parquet-data/my_mm/test-*
- config_name: nb_no
  data_files:
  - split: train
    path: parquet-data/nb_no/train-*
  - split: validation
    path: parquet-data/nb_no/validation-*
  - split: test
    path: parquet-data/nb_no/test-*
- config_name: ne_np
  data_files:
  - split: train
    path: parquet-data/ne_np/train-*
  - split: validation
    path: parquet-data/ne_np/validation-*
  - split: test
    path: parquet-data/ne_np/test-*
- config_name: nl_nl
  data_files:
  - split: train
    path: parquet-data/nl_nl/train-*
  - split: validation
    path: parquet-data/nl_nl/validation-*
  - split: test
    path: parquet-data/nl_nl/test-*
- config_name: nso_za
  data_files:
  - split: train
    path: parquet-data/nso_za/train-*
  - split: validation
    path: parquet-data/nso_za/validation-*
  - split: test
    path: parquet-data/nso_za/test-*
- config_name: ny_mw
  data_files:
  - split: train
    path: parquet-data/ny_mw/train-*
  - split: validation
    path: parquet-data/ny_mw/validation-*
  - split: test
    path: parquet-data/ny_mw/test-*
- config_name: oc_fr
  data_files:
  - split: train
    path: parquet-data/oc_fr/train-*
  - split: validation
    path: parquet-data/oc_fr/validation-*
  - split: test
    path: parquet-data/oc_fr/test-*
- config_name: om_et
  data_files:
  - split: train
    path: parquet-data/om_et/train-*
  - split: validation
    path: parquet-data/om_et/validation-*
  - split: test
    path: parquet-data/om_et/test-*
- config_name: or_in
  data_files:
  - split: train
    path: parquet-data/or_in/train-*
  - split: validation
    path: parquet-data/or_in/validation-*
  - split: test
    path: parquet-data/or_in/test-*
- config_name: pa_in
  data_files:
  - split: train
    path: parquet-data/pa_in/train-*
  - split: validation
    path: parquet-data/pa_in/validation-*
  - split: test
    path: parquet-data/pa_in/test-*
- config_name: pl_pl
  data_files:
  - split: train
    path: parquet-data/pl_pl/train-*
  - split: validation
    path: parquet-data/pl_pl/validation-*
  - split: test
    path: parquet-data/pl_pl/test-*
- config_name: ps_af
  data_files:
  - split: train
    path: parquet-data/ps_af/train-*
  - split: validation
    path: parquet-data/ps_af/validation-*
  - split: test
    path: parquet-data/ps_af/test-*
- config_name: pt_br
  data_files:
  - split: train
    path: parquet-data/pt_br/train-*
  - split: validation
    path: parquet-data/pt_br/validation-*
  - split: test
    path: parquet-data/pt_br/test-*
- config_name: ro_ro
  data_files:
  - split: train
    path: parquet-data/ro_ro/train-*
  - split: validation
    path: parquet-data/ro_ro/validation-*
  - split: test
    path: parquet-data/ro_ro/test-*
- config_name: ru_ru
  data_files:
  - split: train
    path: parquet-data/ru_ru/train-*
  - split: validation
    path: parquet-data/ru_ru/validation-*
  - split: test
    path: parquet-data/ru_ru/test-*
- config_name: sd_in
  data_files:
  - split: train
    path: parquet-data/sd_in/train-*
  - split: validation
    path: parquet-data/sd_in/validation-*
  - split: test
    path: parquet-data/sd_in/test-*
- config_name: sk_sk
  data_files:
  - split: train
    path: parquet-data/sk_sk/train-*
  - split: validation
    path: parquet-data/sk_sk/validation-*
  - split: test
    path: parquet-data/sk_sk/test-*
- config_name: sl_si
  data_files:
  - split: train
    path: parquet-data/sl_si/train-*
  - split: validation
    path: parquet-data/sl_si/validation-*
  - split: test
    path: parquet-data/sl_si/test-*
- config_name: sn_zw
  data_files:
  - split: train
    path: parquet-data/sn_zw/train-*
  - split: validation
    path: parquet-data/sn_zw/validation-*
  - split: test
    path: parquet-data/sn_zw/test-*
- config_name: so_so
  data_files:
  - split: train
    path: parquet-data/so_so/train-*
  - split: validation
    path: parquet-data/so_so/validation-*
  - split: test
    path: parquet-data/so_so/test-*
- config_name: sr_rs
  data_files:
  - split: train
    path: parquet-data/sr_rs/train-*
  - split: validation
    path: parquet-data/sr_rs/validation-*
  - split: test
    path: parquet-data/sr_rs/test-*
- config_name: sv_se
  data_files:
  - split: train
    path: parquet-data/sv_se/train-*
  - split: validation
    path: parquet-data/sv_se/validation-*
  - split: test
    path: parquet-data/sv_se/test-*
- config_name: sw_ke
  data_files:
  - split: train
    path: parquet-data/sw_ke/train-*
  - split: validation
    path: parquet-data/sw_ke/validation-*
  - split: test
    path: parquet-data/sw_ke/test-*
- config_name: ta_in
  data_files:
  - split: train
    path: parquet-data/ta_in/train-*
  - split: validation
    path: parquet-data/ta_in/validation-*
  - split: test
    path: parquet-data/ta_in/test-*
- config_name: te_in
  data_files:
  - split: train
    path: parquet-data/te_in/train-*
  - split: validation
    path: parquet-data/te_in/validation-*
  - split: test
    path: parquet-data/te_in/test-*
- config_name: tg_tj
  data_files:
  - split: train
    path: parquet-data/tg_tj/train-*
  - split: validation
    path: parquet-data/tg_tj/validation-*
  - split: test
    path: parquet-data/tg_tj/test-*
- config_name: th_th
  data_files:
  - split: train
    path: parquet-data/th_th/train-*
  - split: validation
    path: parquet-data/th_th/validation-*
  - split: test
    path: parquet-data/th_th/test-*
- config_name: tr_tr
  data_files:
  - split: train
    path: parquet-data/tr_tr/train-*
  - split: validation
    path: parquet-data/tr_tr/validation-*
  - split: test
    path: parquet-data/tr_tr/test-*
- config_name: uk_ua
  data_files:
  - split: train
    path: parquet-data/uk_ua/train-*
  - split: validation
    path: parquet-data/uk_ua/validation-*
  - split: test
    path: parquet-data/uk_ua/test-*
- config_name: umb_ao
  data_files:
  - split: train
    path: parquet-data/umb_ao/train-*
  - split: validation
    path: parquet-data/umb_ao/validation-*
  - split: test
    path: parquet-data/umb_ao/test-*
- config_name: ur_pk
  data_files:
  - split: train
    path: parquet-data/ur_pk/train-*
  - split: validation
    path: parquet-data/ur_pk/validation-*
  - split: test
    path: parquet-data/ur_pk/test-*
- config_name: uz_uz
  data_files:
  - split: train
    path: parquet-data/uz_uz/train-*
  - split: validation
    path: parquet-data/uz_uz/validation-*
  - split: test
    path: parquet-data/uz_uz/test-*
- config_name: vi_vn
  data_files:
  - split: train
    path: parquet-data/vi_vn/train-*
  - split: validation
    path: parquet-data/vi_vn/validation-*
  - split: test
    path: parquet-data/vi_vn/test-*
- config_name: wo_sn
  data_files:
  - split: train
    path: parquet-data/wo_sn/train-*
  - split: validation
    path: parquet-data/wo_sn/validation-*
  - split: test
    path: parquet-data/wo_sn/test-*
- config_name: xh_za
  data_files:
  - split: train
    path: parquet-data/xh_za/train-*
  - split: validation
    path: parquet-data/xh_za/validation-*
  - split: test
    path: parquet-data/xh_za/test-*
- config_name: yo_ng
  data_files:
  - split: train
    path: parquet-data/yo_ng/train-*
  - split: validation
    path: parquet-data/yo_ng/validation-*
  - split: test
    path: parquet-data/yo_ng/test-*
- config_name: yue_hant_hk
  data_files:
  - split: train
    path: parquet-data/yue_hant_hk/train-*
  - split: validation
    path: parquet-data/yue_hant_hk/validation-*
  - split: test
    path: parquet-data/yue_hant_hk/test-*
- config_name: zu_za
  data_files:
  - split: train
    path: parquet-data/zu_za/train-*
  - split: validation
    path: parquet-data/zu_za/validation-*
  - split: test
    path: parquet-data/zu_za/test-*
---

# FLEURS

## Dataset Description

- **Fine-Tuning script:** [pytorch/speech-recognition](https://github.com/huggingface/transformers/tree/main/examples/pytorch/speech-recognition)
- **Paper:** [FLEURS: Few-shot Learning Evaluation of
Universal Representations of Speech](https://arxiv.org/abs/2205.12446)
- **Total amount of disk used:** ca. 350 GB

Fleurs is the speech version of the [FLoRes machine translation benchmark](https://arxiv.org/abs/2106.03193). 
We use 2009 n-way parallel sentences from the FLoRes dev and devtest publicly available sets, in 102 languages. 

Training sets have around 10 hours of supervision. Speakers of the train sets are different than speakers from the dev/test sets. Multilingual fine-tuning is
used and ”unit error rate” (characters, signs) of all languages is averaged. Languages and results are also grouped into seven geographical areas: 

- **Western Europe**: *Asturian, Bosnian, Catalan, Croatian, Danish, Dutch, English, Finnish, French, Galician, German, Greek, Hungarian, Icelandic, Irish, Italian, Kabuverdianu, Luxembourgish, Maltese, Norwegian, Occitan, Portuguese, Spanish, Swedish, Welsh* 
- **Eastern Europe**: *Armenian, Belarusian, Bulgarian, Czech, Estonian, Georgian, Latvian, Lithuanian, Macedonian, Polish, Romanian, Russian, Serbian, Slovak, Slovenian, Ukrainian*
- **Central-Asia/Middle-East/North-Africa**: *Arabic, Azerbaijani, Hebrew, Kazakh, Kyrgyz, Mongolian, Pashto, Persian, Sorani-Kurdish, Tajik, Turkish, Uzbek*
- **Sub-Saharan Africa**: *Afrikaans, Amharic, Fula, Ganda, Hausa, Igbo, Kamba, Lingala, Luo, Northern-Sotho, Nyanja, Oromo, Shona, Somali, Swahili, Umbundu, Wolof, Xhosa, Yoruba, Zulu*
- **South-Asia**: *Assamese, Bengali, Gujarati, Hindi, Kannada, Malayalam, Marathi, Nepali, Oriya, Punjabi, Sindhi, Tamil, Telugu, Urdu*
- **South-East Asia**: *Burmese, Cebuano, Filipino, Indonesian, Javanese, Khmer, Lao, Malay, Maori, Thai, Vietnamese*
- **CJK languages**: *Cantonese and Mandarin Chinese, Japanese, Korean*


## How to use & Supported Tasks

### How to use

The `datasets` library allows you to load and pre-process your dataset in pure Python, at scale. The dataset can be downloaded and prepared in one call to your local drive by using the `load_dataset` function. 

For example, to download the Hindi config, simply specify the corresponding language config name (i.e., "hi_in" for Hindi):
```python
from datasets import load_dataset
fleurs = load_dataset("google/fleurs", "hi_in", split="train")
```

Using the datasets library, you can also stream the dataset on-the-fly by adding a `streaming=True` argument to the `load_dataset` function call. Loading a dataset in streaming mode loads individual samples of the dataset at a time, rather than downloading the entire dataset to disk.
```python
from datasets import load_dataset
fleurs = load_dataset("google/fleurs", "hi_in", split="train", streaming=True)
print(next(iter(fleurs)))
```

*Bonus*: create a [PyTorch dataloader](https://huggingface.co/docs/datasets/use_with_pytorch) directly with your own datasets (local/streamed).

Local:

```python
from datasets import load_dataset
from torch.utils.data.sampler import BatchSampler, RandomSampler
fleurs = load_dataset("google/fleurs", "hi_in", split="train")
batch_sampler = BatchSampler(RandomSampler(fleurs), batch_size=32, drop_last=False)
dataloader = DataLoader(fleurs, batch_sampler=batch_sampler)
```

Streaming:

```python
from datasets import load_dataset
from torch.utils.data import DataLoader
fleurs = load_dataset("google/fleurs", "hi_in", split="train")
dataloader = DataLoader(fleurs, batch_size=32)
```

To find out more about loading and preparing audio datasets, head over to [hf.co/blog/audio-datasets](https://huggingface.co/blog/audio-datasets).

### Example scripts

Train your own CTC or Seq2Seq Automatic Speech Recognition models on FLEURS with `transformers` - [here](https://github.com/huggingface/transformers/tree/main/examples/pytorch/speech-recognition).

Fine-tune your own Language Identification models on FLEURS with `transformers` - [here](https://github.com/huggingface/transformers/tree/main/examples/pytorch/audio-classification)

### 1. Speech Recognition (ASR)

```py
from datasets import load_dataset

fleurs_asr = load_dataset("google/fleurs", "af_za")  # for Afrikaans
# to download all data for multi-lingual fine-tuning uncomment following line
# fleurs_asr = load_dataset("google/fleurs", "all")

# see structure
print(fleurs_asr)

# load audio sample on the fly
audio_input = fleurs_asr["train"][0]["audio"]  # first decoded audio sample
transcription = fleurs_asr["train"][0]["transcription"]  # first transcription
# use `audio_input` and `transcription` to fine-tune your model for ASR

# for analyses see language groups
all_language_groups = fleurs_asr["train"].features["lang_group_id"].names
lang_group_id = fleurs_asr["train"][0]["lang_group_id"]

all_language_groups[lang_group_id]
```

### 2. Language Identification

LangID can often be a domain classification, but in the case of FLEURS-LangID, recordings are done in a similar setting across languages and the utterances correspond to n-way parallel sentences, in the exact same domain, making this task particularly relevant for evaluating LangID. The setting is simple, FLEURS-LangID is splitted in train/valid/test for each language. We simply create a single train/valid/test for LangID by merging all.

```py
from datasets import load_dataset

fleurs_langID = load_dataset("google/fleurs", "all") # to download all data

# see structure
print(fleurs_langID)

# load audio sample on the fly
audio_input = fleurs_langID["train"][0]["audio"]  # first decoded audio sample
language_class = fleurs_langID["train"][0]["lang_id"]  # first id class
language = fleurs_langID["train"].features["lang_id"].names[language_class]

# use audio_input and language_class to fine-tune your model for audio classification
```

### 3. Retrieval

Retrieval provides n-way parallel speech and text data. Similar to how XTREME for text leverages Tatoeba to evaluate bitext mining a.k.a sentence translation retrieval, we use Retrieval to evaluate the quality of fixed-size representations of speech utterances. Our goal is to incentivize the creation of fixed-size speech encoder for speech retrieval. The system has to retrieve the English "key" utterance corresponding to the speech translation of "queries" in 15 languages. Results have to be reported on the test sets of Retrieval whose utterances are used as queries (and keys for English). We augment the English keys with a large number of utterances to make the task more difficult.

```py
from datasets import load_dataset

fleurs_retrieval = load_dataset("google/fleurs", "af_za")  # for Afrikaans
# to download all data for multi-lingual fine-tuning uncomment following line
# fleurs_retrieval = load_dataset("google/fleurs", "all")

# see structure
print(fleurs_retrieval)

# load audio sample on the fly
audio_input = fleurs_retrieval["train"][0]["audio"]  # decoded audio sample
text_sample_pos = fleurs_retrieval["train"][0]["transcription"]  # positive text sample
text_sample_neg = fleurs_retrieval["train"][1:20]["transcription"] # negative text samples

# use `audio_input`, `text_sample_pos`, and `text_sample_neg` to fine-tune your model for retrieval
```

Users can leverage the training (and dev) sets of FLEURS-Retrieval with a ranking loss to build better cross-lingual fixed-size representations of speech.

## Dataset Structure

We show detailed information the example configurations `af_za` of the dataset.
All other configurations have the same structure.

### Data Instances

**af_za**
- Size of downloaded dataset files: 1.47 GB
- Size of the generated dataset: 1 MB
- Total amount of disk used: 1.47 GB

An example of a data instance of the config `af_za` looks as follows:

```
{'id': 91,
 'num_samples': 385920,
 'path': '/home/patrick/.cache/huggingface/datasets/downloads/extracted/310a663d52322700b3d3473cbc5af429bd92a23f9bc683594e70bc31232db39e/home/vaxelrod/FLEURS/oss2_obfuscated/af_za/audio/train/17797742076841560615.wav',
 'audio': {'path': '/home/patrick/.cache/huggingface/datasets/downloads/extracted/310a663d52322700b3d3473cbc5af429bd92a23f9bc683594e70bc31232db39e/home/vaxelrod/FLEURS/oss2_obfuscated/af_za/audio/train/17797742076841560615.wav',
  'array': array([ 0.0000000e+00,  0.0000000e+00,  0.0000000e+00, ...,
         -1.1205673e-04, -8.4638596e-05, -1.2731552e-04], dtype=float32),
  'sampling_rate': 16000},
 'raw_transcription': 'Dit is nog nie huidiglik bekend watter aantygings gemaak sal word of wat owerhede na die seun gelei het nie maar jeugmisdaad-verrigtinge het in die federale hof begin',
 'transcription': 'dit is nog nie huidiglik bekend watter aantygings gemaak sal word of wat owerhede na die seun gelei het nie maar jeugmisdaad-verrigtinge het in die federale hof begin',
 'gender': 0,
 'lang_id': 0,
 'language': 'Afrikaans',
 'lang_group_id': 3}
```

### Data Fields

The data fields are the same among all splits.
- **id** (int): ID of audio sample
- **num_samples** (int): Number of float values
- **path** (str): Path to the audio file
- **audio** (dict): Audio object including loaded audio array, sampling rate and path ot audio
- **raw_transcription** (str): The non-normalized transcription of the audio file
- **transcription** (str): Transcription of the audio file
- **gender** (int): Class id of gender
- **lang_id** (int): Class id of language
- **lang_group_id** (int): Class id of language group

### Data Splits

Every config only has the `"train"` split containing of *ca.* 1000 examples, and a `"validation"` and `"test"` split each containing of *ca.* 400 examples.

## Dataset Creation

We collect between one and three recordings for each sentence (2.3 on average), and buildnew train-dev-test splits with 1509, 150 and 350 sentences for
train, dev and test respectively.

## Considerations for Using the Data

### Social Impact of Dataset

This dataset is meant to encourage the development of speech technology in a lot more languages of the world. One of the goal is to give equal access to technologies like speech recognition or speech translation to everyone, meaning better dubbing or better access to content from the internet (like podcasts, streaming or videos).

### Discussion of Biases

Most datasets have a fair distribution of gender utterances (e.g. the newly introduced FLEURS dataset). While many languages are covered from various regions of the world, the benchmark misses many languages that are all equally important. We believe technology built through FLEURS should generalize to all languages.

### Other Known Limitations

The dataset has a particular focus on read-speech because common evaluation benchmarks like CoVoST-2 or LibriSpeech evaluate on this type of speech. There is sometimes a known mismatch between performance obtained in a read-speech setting and a more noisy setting (in production for instance). Given the big progress that remains to be made on many languages, we believe better performance on FLEURS should still correlate well with actual progress made for speech understanding.

## Additional Information

All datasets are licensed under the [Creative Commons license (CC-BY)](https://creativecommons.org/licenses/).

### Citation Information

You can access the FLEURS paper at https://arxiv.org/abs/2205.12446.
Please cite the paper when referencing the FLEURS corpus as:

```
@article{fleurs2022arxiv,
  title = {FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech},
  author = {Conneau, Alexis and Ma, Min and Khanuja, Simran and Zhang, Yu and Axelrod, Vera and Dalmia, Siddharth and Riesa, Jason and Rivera, Clara and Bapna, Ankur},
  journal={arXiv preprint arXiv:2205.12446},
  url = {https://arxiv.org/abs/2205.12446},
  year = {2022},
```

### Contributions

Thanks to [@patrickvonplaten](https://github.com/patrickvonplaten) and [@aconneau](https://github.com/aconneau) for adding this dataset.
