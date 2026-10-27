---
annotations_creators:
- expert-generated
- crowdsourced
- machine-generated
language_creators:
- crowdsourced
- expert-generated
language:
- en
- fr
- it
- es
- pt
- de
- nl
- ru
- pl
- cs
- ko
- zh
license:
- cc-by-4.0
multilinguality:
- multilingual
size_categories:
- 10K<n<100K
task_categories:
- automatic-speech-recognition
task_ids:
- keyword-spotting
pretty_name: MInDS-14
language_bcp47:
- en
- en-GB
- en-US
- en-AU
- fr
- it
- es
- pt
- de
- nl
- ru
- pl
- cs
- ko
- zh
tags:
- speech-recognition
configs:
- config_name: all
  data_files:
  - split: train
    path: all/train-*
- config_name: cs-CZ
  data_files:
  - split: train
    path: cs-CZ/train-*
- config_name: de-DE
  data_files:
  - split: train
    path: de-DE/train-*
- config_name: en-AU
  data_files:
  - split: train
    path: en-AU/train-*
- config_name: en-GB
  data_files:
  - split: train
    path: en-GB/train-*
- config_name: en-US
  data_files:
  - split: train
    path: en-US/train-*
- config_name: es-ES
  data_files:
  - split: train
    path: es-ES/train-*
- config_name: fr-FR
  data_files:
  - split: train
    path: fr-FR/train-*
- config_name: it-IT
  data_files:
  - split: train
    path: it-IT/train-*
- config_name: ko-KR
  data_files:
  - split: train
    path: ko-KR/train-*
- config_name: nl-NL
  data_files:
  - split: train
    path: nl-NL/train-*
- config_name: pl-PL
  data_files:
  - split: train
    path: pl-PL/train-*
- config_name: pt-PT
  data_files:
  - split: train
    path: pt-PT/train-*
- config_name: ru-RU
  data_files:
  - split: train
    path: ru-RU/train-*
- config_name: zh-CN
  data_files:
  - split: train
    path: zh-CN/train-*
dataset_info:
- config_name: all
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 628290192.68
    num_examples: 8168
  download_size: 566674935
  dataset_size: 628290192.68
- config_name: cs-CZ
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 40369391.0
    num_examples: 574
  download_size: 36473997
  dataset_size: 40369391.0
- config_name: de-DE
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 53448213.0
    num_examples: 611
  download_size: 41073246
  dataset_size: 53448213.0
- config_name: en-AU
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 44154982.0
    num_examples: 654
  download_size: 37348052
  dataset_size: 44154982.0
- config_name: en-GB
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 39143835.0
    num_examples: 592
  download_size: 34551079
  dataset_size: 39143835.0
- config_name: en-US
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 38787013.0
    num_examples: 563
  download_size: 34196221
  dataset_size: 38787013.0
- config_name: es-ES
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 44143874.0
    num_examples: 486
  download_size: 39069577
  dataset_size: 44143874.0
- config_name: fr-FR
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 36200685.0
    num_examples: 539
  download_size: 32613161
  dataset_size: 36200685.0
- config_name: it-IT
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 82852403.0
    num_examples: 696
  download_size: 59299376
  dataset_size: 82852403.0
- config_name: ko-KR
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 39733949.0
    num_examples: 592
  download_size: 34163604
  dataset_size: 39733949.0
- config_name: nl-NL
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 51418818.0
    num_examples: 654
  download_size: 46536858
  dataset_size: 51418818.0
- config_name: pl-PL
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 88547861.0
    num_examples: 562
  download_size: 52662883
  dataset_size: 88547861.0
- config_name: pt-PT
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 77549349.0
    num_examples: 604
  download_size: 51738310
  dataset_size: 77549349.0
- config_name: ru-RU
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 38159953.0
    num_examples: 539
  download_size: 34494545
  dataset_size: 38159953.0
- config_name: zh-CN
  features:
  - name: path
    dtype: string
  - name: audio
    dtype:
      audio:
        sampling_rate: 8000
  - name: transcription
    dtype: string
  - name: english_transcription
    dtype: string
  - name: intent_class
    dtype:
      class_label:
        names:
          '0': abroad
          '1': address
          '2': app_error
          '3': atm_limit
          '4': balance
          '5': business_loan
          '6': card_issues
          '7': cash_deposit
          '8': direct_debit
          '9': freeze
          '10': high_value_payment
          '11': joint_account
          '12': latest_transactions
          '13': pay_bill
  - name: lang_id
    dtype:
      class_label:
        names:
          '0': cs-CZ
          '1': de-DE
          '2': en-AU
          '3': en-GB
          '4': en-US
          '5': es-ES
          '6': fr-FR
          '7': it-IT
          '8': ko-KR
          '9': nl-NL
          '10': pl-PL
          '11': pt-PT
          '12': ru-RU
          '13': zh-CN
  splits:
  - name: train
    num_bytes: 36522343.0
    num_examples: 502
  download_size: 32357378
  dataset_size: 36522343.0
---

# MInDS-14

## Dataset Description

- **Fine-Tuning script:** [pytorch/audio-classification](https://github.com/huggingface/transformers/tree/main/examples/pytorch/audio-classification)
- **Paper:** [Multilingual and Cross-Lingual Intent Detection from Spoken Data](https://arxiv.org/abs/2104.08524)
- **Total amount of disk used:** ca. 500 MB 

MINDS-14 is training and evaluation resource for intent detection task with spoken data. It covers 14 
intents extracted from a commercial system in the e-banking domain, associated with spoken examples in 14 diverse language varieties.

## Example

MInDS-14 can be downloaded and used as follows:

```py
from datasets import load_dataset

minds_14 = load_dataset("PolyAI/minds14", "fr-FR") # for French
# to download all data for multi-lingual fine-tuning uncomment following line
# minds_14 = load_dataset("PolyAI/all", "all")

# see structure
print(minds_14)

# load audio sample on the fly
audio_input = minds_14["train"][0]["audio"]  # first decoded audio sample
intent_class = minds_14["train"][0]["intent_class"]  # first transcription
intent = minds_14["train"].features["intent_class"].names[intent_class]

# use audio_input and language_class to fine-tune your model for audio classification
```

## Dataset Structure

We show detailed information the example configurations `fr-FR` of the dataset.
All other configurations have the same structure.

### Data Instances

**fr-FR**

- Size of downloaded dataset files: 471 MB
- Size of the generated dataset: 300 KB
- Total amount of disk used: 471 MB


An example of a datainstance of the config `fr-FR` looks as follows:

```
{
    "path": "fr-FR~ADDRESS/response_4.wav",
    "audio": {
        "array": array(
            [0.0, 0.0, 0.0, ..., 0.0, 0.00048828, -0.00024414], dtype=float32
        ),
        "sampling_rate": 8000,
    },
    "transcription": "je souhaite changer mon adresse",
    "english_transcription": "I want to change my address",
    "intent_class": 1,
    "lang_id": 6,
}
```

### Data Fields
The data fields are the same among all splits.

- **path** (str): Path to the audio file
- **audio** (dict): Audio object including loaded audio array, sampling rate and path ot audio
- **transcription** (str): Transcription of the audio file
- **english_transcription** (str): English transcription of the audio file
- **intent_class** (int): Class id of intent
- **lang_id** (int): Id of language

### Data Splits
Every config only has the `"train"` split containing of *ca.* 600 examples.

## Dataset Creation

[More Information Needed](https://github.com/huggingface/datasets/blob/master/CONTRIBUTING.md#how-to-contribute-to-the-dataset-cards)

## Considerations for Using the Data

### Social Impact of Dataset

[More Information Needed](https://github.com/huggingface/datasets/blob/master/CONTRIBUTING.md#how-to-contribute-to-the-dataset-cards)

### Discussion of Biases

[More Information Needed](https://github.com/huggingface/datasets/blob/master/CONTRIBUTING.md#how-to-contribute-to-the-dataset-cards)

### Other Known Limitations

[More Information Needed](https://github.com/huggingface/datasets/blob/master/CONTRIBUTING.md#how-to-contribute-to-the-dataset-cards)

## Additional Information

### Dataset Curators

[More Information Needed](https://github.com/huggingface/datasets/blob/master/CONTRIBUTING.md#how-to-contribute-to-the-dataset-cards)

### Licensing Information

All datasets are licensed under the [Creative Commons license (CC-BY)](https://creativecommons.org/licenses/).

### Citation Information

```
@article{DBLP:journals/corr/abs-2104-08524,
  author    = {Daniela Gerz and
               Pei{-}Hao Su and
               Razvan Kusztos and
               Avishek Mondal and
               Michal Lis and
               Eshan Singhal and
               Nikola Mrksic and
               Tsung{-}Hsien Wen and
               Ivan Vulic},
  title     = {Multilingual and Cross-Lingual Intent Detection from Spoken Data},
  journal   = {CoRR},
  volume    = {abs/2104.08524},
  year      = {2021},
  url       = {https://arxiv.org/abs/2104.08524},
  eprinttype = {arXiv},
  eprint    = {2104.08524},
  timestamp = {Mon, 26 Apr 2021 17:25:10 +0200},
  biburl    = {https://dblp.org/rec/journals/corr/abs-2104-08524.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}
```

### Contributions

Thanks to [@patrickvonplaten](https://github.com/patrickvonplaten) for adding this dataset
