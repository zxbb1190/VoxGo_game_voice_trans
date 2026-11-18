# Historical acceptance evidence

These are immutable records of specific past runs, not active source code or proof of current release status.
Use [the testing guide](../README.md) for current commands and [the release procedure](../../release_process.md) for releases.

Keep original paths and bytes: reports, provenance, hashes and external links may reference them.
Store routine CI logs and coverage in Actions artifacts (14-day retention), not new evidence snapshots.
Add a historical batch only for an explicit release or acceptance record; exclude keys and user configuration.

Tracked batches: **32**; files: **1,251**; bytes: **38,408,076**.

Regenerate with `python scripts/index_test_evidence.py --write`; verify with `--check`.
Sizes and tree hashes cover Git blob bytes and sorted relative paths, independent of checkout line endings.
Stage new evidence files before regenerating; the index intentionally ignores untracked local output.

| Batch | Files | Bytes | SHA-256 tree digest |
|---|---:|---:|---|
| [v0.5.3-asr-translation-comparison](v0.5.3-asr-translation-comparison/) | 4 | 74,339 | `737393dd4b3763f30d65ae7931a69a6d6c5a75f2a509bd226fdf00263de5b0a1` |
| [v0.5.3-beta-blockers-2026-10-28](v0.5.3-beta-blockers-2026-10-28/) | 33 | 1,623,995 | `456b75d000f07bde3ae73d28ee6f7e234a9bcfe5c3dda7b1137e5984bb394b51` |
| [v0.5.3-beta-blockers-online-2026-10-28](v0.5.3-beta-blockers-online-2026-10-28/) | 36 | 539,063 | `771134d2a3d946fa607af0a55b6cd3422a0cab92094706c24f8e31343695d4b8` |
| [v0.5.3-beta-final-2026-10-28](v0.5.3-beta-final-2026-10-28/) | 27 | 300,272 | `6461761d4e7b1e882f6d1c7fb19e63b9141c2cc5a92769bf250c1d70bd2232b8` |
| [v0.5.3-chinese-source-display-2026-10-28](v0.5.3-chinese-source-display-2026-10-28/) | 17 | 67,650 | `9ae31f770de0a00ff849b829a0c27a3e3caa7e65e30a92fcb88f14bd00a6112a` |
| [v0.5.3-five-language-beta-2026-10-27](v0.5.3-five-language-beta-2026-10-27/) | 506 | 13,649,715 | `c8b20b73d0d34e6ba8609004d05c8a1768129363631a4e4ce75298160dc7d8c7` |
| [v0.5.3-multilingual-online](v0.5.3-multilingual-online/) | 12 | 186,193 | `190470b35ab653d50a0f8dc3dde9b7061b28dbabf4f2951936a48721df416fce` |
| [v0.5.3-online-entry](v0.5.3-online-entry/) | 4 | 5,003 | `42b3dc67462e4e3ee6e8219f4922b48ed0df0985eba4c6cfda9e64c8200d96ef` |
| [v0.5.3-online-user-smoke](v0.5.3-online-user-smoke/) | 4 | 75,370 | `8e0cd67d88877c5de97756dd2385c2632c879610d8cd668fbadb5b0688416a06` |
| [v0.5.3-paired-speech-2026-10-27](v0.5.3-paired-speech-2026-10-27/) | 46 | 243,290 | `94eccb31702f066dd8f3a89cbf9c244cb6d92c600b1ded59e238990d66625c4d` |
| [v0.5.3-prompt-ab-2026-10-28](v0.5.3-prompt-ab-2026-10-28/) | 44 | 583,921 | `28ae6ca4076764dc1f745ba8ea9176d171989dc50bfbdef8bef29c27952f2172` |
| [v0.5.3-released-speech-compatibility-2026-10-28](v0.5.3-released-speech-compatibility-2026-10-28/) | 9 | 36,529 | `e78abbe385e0a5c3e4b515f42dd0e6cc2957e637be0642ccf8ee7f4eb2584ae9` |
| [v0.5.3-ru-capture-ab-2026-10-27](v0.5.3-ru-capture-ab-2026-10-27/) | 40 | 2,658,898 | `c2e3753625a506594dd25dac886bdd42bd2e260dd78e9c231058d94347907395` |
| [v0.5.3-ru-continuous-2026-10-27](v0.5.3-ru-continuous-2026-10-27/) | 131 | 9,970,079 | `241251961d2e5399c6e3fa5fdb295a2de70f729d9472c2eba3a7bdf8f84d6925` |
| [v0.5.3-ru-tail-context-2026-10-27](v0.5.3-ru-tail-context-2026-10-27/) | 16 | 298,343 | `3085f0dac11b39e905e648058c441e39fab68d6658c5849ba7a89f79c4b92e66` |
| [v0.5.3-ru-tail-diagnostic-2026-10-27](v0.5.3-ru-tail-diagnostic-2026-10-27/) | 16 | 234,407 | `4a824e6226ae6fc5b9bb3323b6bd6766f5feb9f9ee6458c7ca2079bbb7e06228` |
| [v0.5.3-source-asr-policy-2026-10-28](v0.5.3-source-asr-policy-2026-10-28/) | 7 | 28,660 | `e1066bcb0bea0e21f5f06825f2400e2aa21b21f8583bb5aa1d78be0eafdd6b00` |
| [v0.5.3-speech-repair](v0.5.3-speech-repair/) | 16 | 405,036 | `953595f0ab573cd1a79420bb8be3b714500643fbdb11957a0efddd695457685e` |
| [v0.5.3-ui-five-language-2026-10-28](v0.5.3-ui-five-language-2026-10-28/) | 30 | 321,244 | `282efebefd38ece37cf04757dd840b0ed97308335c873cd8915ad1c6f51031a7` |
| [v0.5.3-windows-acceptance](v0.5.3-windows-acceptance/) | 8 | 93,950 | `10742d90e06e92e01aebaa7cb27a701e37cecd07a5b4cb7ca11de8391d1eabeb` |
| [v0.6.0-beta-presentation-2026-10-29](v0.6.0-beta-presentation-2026-10-29/) | 39 | 1,224,744 | `37bcf52a0a382aceab746e9e9d72ef1e6b8f155c7e395b28c36200e77a828879` |
| [v0.6.0-eager-model-2026-10-29](v0.6.0-eager-model-2026-10-29/) | 17 | 89,823 | `ca980413186825f255f1501f616c6f1799fc67648eb4f285d2fcf34e90458fe5` |
| [v0.6.0-hero-brand-2026-10-29](v0.6.0-hero-brand-2026-10-29/) | 14 | 1,209,732 | `4bc3491b65b269986b3fa6273eff7921e4fcb8d8811a0881fa953fcf05cb7a6d` |
| [v0.6.0-language-usage-2026-10-29](v0.6.0-language-usage-2026-10-29/) | 15 | 661,105 | `e03f78d8d2f37efa260cf5475ebfab96e020a48c812b6d1d165bacfadf89a22d` |
| [v0.6.0-language-usage-release-2026-10-30](v0.6.0-language-usage-release-2026-10-30/) | 23 | 229,151 | `17a75a410170734cd8fb42f1a601f8004d10dfcaadcdd86b169bcc8ff20fa05f` |
| [v0.6.0-lite-rebuild-2026-10-29](v0.6.0-lite-rebuild-2026-10-29/) | 12 | 52,059 | `92fb0d020965e4612c5899dcb174a2820c78acb3584c0b5a3a9866c91e3953a4` |
| [v0.6.0-model-preparation-feedback-2026-10-29](v0.6.0-model-preparation-feedback-2026-10-29/) | 14 | 229,110 | `f2c4726a7f0b82603f0d2a252aea4822ce9347f70272c0dd2fb1927bbd74c51e` |
| [v0.6.0-packaging-2026-10-28](v0.6.0-packaging-2026-10-28/) | 27 | 105,725 | `f2a4cc9545db548fdedcbb97002263fdebc67528bd71ccaac89f0025d0f5e32c` |
| [v0.6.0-site-five-locales-2026-10-29](v0.6.0-site-five-locales-2026-10-29/) | 35 | 2,378,965 | `06dfa94f2895da5cb05cc60eec6575aebd87707bd53d318b1314b0fdd2a8aeb8` |
| [v0.6.0-startup-fix-2026-10-28](v0.6.0-startup-fix-2026-10-28/) | 27 | 200,042 | `53537a21b6cb48dae213cd2addfd7049c6ac9dfa48393f73f76ea5b8199f17c3` |
| [v0.6.0-today-classifications-2026-10-30](v0.6.0-today-classifications-2026-10-30/) | 18 | 598,330 | `9fa03cd58445edf82f2de40026339c9938f2413c47b677fa8b824c91079503f1` |
| [v0.6.0-workspace-closeout-2026-10-28](v0.6.0-workspace-closeout-2026-10-28/) | 4 | 33,333 | `29e0d16fc86c85b51b0555d71ce04c0f70bd7750423fc00c541efc3b9f0060e3` |
