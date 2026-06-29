# VoxGo

Chinese documentation: [README.md](README.md)

VoxGo is an open-source real-time voice translation overlay for PC gamers, designed for overseas servers, guild voice chat, Discord teammates, and live-stream subtitle assistance.

Website: <https://voxgo.cn/><br>
GitHub: <https://github.com/zxbb1190/VoxGo_game_voice_trans>

## Features
- **First-run setup wizard**: The first launch walks the player through translation and audio tests, then saves `setup_completed`.
- **API Key test**: The wizard and settings dialog can make one real translation request to verify the Key, model, and endpoint.
- **Audio device test**: Opens the selected device and shows a live level bar so players can confirm game/Discord/video audio is detected.
- **System-audio capture**: Captures Windows playback audio through WASAPI Loopback, not the microphone.
- **Local speech recognition**: Uses faster-whisper for offline speech-to-text, currently with fixed English or Chinese recognition.
- **English-Chinese translation**: Officially supports English ↔ Chinese today. Choose the recognition language and translation target from the overlay title bar, with one-click swap.
- **Multiple translation providers**: Supports OpenAI-compatible Chat Completions APIs and Google Cloud Translation Basic v2.
- **In-game overlay**: Transparent always-on-top PyQt overlay for translation results.
- **Visible status and error messages**: Startup status, selected audio device, pause/resume events, API status codes, and provider error messages are shown in the overlay.
- **Debug and feedback loop**: Debug mode records the latest recognition/translation/overlay latency, and the feedback button generates a diagnostic template.
- **Mobile mirror**: Pushes translations to a browser on the same LAN through WebSocket.
- **Global hotkeys**: Toggle overlay, clear history, pause/resume translation, plus optional lock and compact-mode hotkeys in settings.

## Project Layout
```text
VoxGo_game_voice_trans/
├── main.py               # Launcher
├── voxgo/                # Application package
│   ├── app.py            # VoxGoApp lifecycle coordinator
│   ├── config/           # Config schema, loading, migration, and presets
│   ├── audio/            # Audio capture, devices, and segmentation
│   ├── asr/              # Whisper recognition and model download
│   ├── translation/      # Translation providers and prompts
│   ├── runtime/          # Runtime events and work items
│   ├── ui/               # Overlay, settings, tray, QR, and dialogs
│   ├── mobile/           # Mobile server and static assets
│   └── update/           # Update checker
├── tests/                # Lightweight automated tests
├── diagnostics/          # Manual troubleshooting scripts
├── config.example.json   # Configuration template
├── config.json           # Local config, ignored by Git
├── requirements.txt      # Python dependencies
├── install.bat           # Windows installer script
├── run.bat               # Windows launcher
├── assets/voxgo.ico      # Windows desktop/installer icon
├── docs/                 # Website and brand assets
├── README.md             # Chinese documentation
└── README_EN.md          # English documentation
```

Run automated tests with:
```bash
python -m unittest discover -s tests
```

Manual troubleshooting scripts live in `diagnostics/`, including import checks, translation API checks, and mobile QR generation. Scripts that call real APIs read the local `config.json` and are not part of normal startup or packaging.

## Player Quick Start

### 1. Download Or Install
Double-click `install.bat`, or run:
```bash
pip install -r requirements.txt
```

If you use a portable Release package, unzip it and run `VoxGo.exe`. The current Release provides 3 packages:

| Package | Contents | Best for |
|---------|----------|----------|
| Lite | No Whisper model, no CUDA DLLs, smallest archive; downloads the model on first use | Most users who can download the model |
| Full | Bundled multilingual Whisper small/base models, no CUDA DLLs | CPU users with unstable model-download networks |
| Full-CUDA / GPU | Bundled multilingual Whisper small/base models plus CUDA DLLs | NVIDIA users who want GPU recognition immediately |

Lite and Full do not download CUDA DLLs at startup. CUDA is checked only when you explicitly select `NVIDIA GPU / CUDA` in settings. VoxGo detects the current GPU first: AMD/Intel users get a clear "GPU unavailable" notice and keep the previous device; NVIDIA users without bundled CUDA DLLs are prompted while VoxGo downloads the CUDA runtime from the current Release into the app folder, then GPU takes effect after restart.

Full and Full-CUDA do not bundle the English-only `small.en` / `base.en` models. VoxGo downloads them on demand only after you enable the English Fast Path / Pure English environment, so users who do not need that path do not pay the extra package size.

### 2. Complete The First-Run Wizard
The first launch opens the setup wizard before Whisper starts loading. Complete this loop:
- Choose a translation provider and fill in the API Key, model name, and compatible endpoint.
- Click "Test API Key" to confirm the real translation API returns a result.
- Choose a `[System Audio]` / `Loopback` audio device.
- Click "Test Audio", play game, Discord, or video voice, and confirm the level bar moves and shows sound detected.
- Click "Finish And Start"; the app saves `app.setup_completed=true` in `user_settings.json`, then starts loading the recognizer.

Clicking "Set Up Later And Start" or closing the wizard also continues startup. You can reopen the gear settings later to retest the API Key and audio device.

### 3. Configure Translation API Manually (Optional)
Copy the example config first:
```bat
copy config.example.json config.json
```

Then edit `config.json`, or start the app and use the gear button in the overlay to choose a translation provider and enter its API Key.

The default provider is OpenAI-compatible:
```json
"translation": {
  "provider": "openai_compatible",
  "api_key": "YOUR_OPENAI_COMPATIBLE_API_KEY",
  "model": "tencent/Hunyuan-MT-7B",
  "endpoint": "https://api.siliconflow.cn/v1/chat/completions"
}
```

The default template uses SiliconFlow with `tencent/Hunyuan-MT-7B`, a free translation model. Register and create an API Key to use it. Availability and quota are subject to the provider's current policy.

Register/get API Key: <https://cloud.siliconflow.cn/i/iA6DF2nP>

Note: SiliconFlow account or quota access may require Alipay real-name or face verification, which may not be available to some users outside mainland China. If you cannot complete that verification, use Google Cloud Translation, DeepSeek, Qwen, GLM, or a local model service instead.

Common OpenAI-compatible examples:

| Provider | Compatible endpoint example | Model example |
|----------|-----------------------------|---------------|
| SiliconFlow | `https://api.siliconflow.cn/v1/chat/completions` | `tencent/Hunyuan-MT-7B` |
| DeepSeek | `https://api.deepseek.com/chat/completions` | `deepseek-v4-flash` |
| Qwen / Alibaba Model Studio | `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` | `qwen-plus` |
| GLM / Zhipu | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | `glm-4.7` |
| Local model | `http://127.0.0.1:11434/v1/chat/completions` or `http://127.0.0.1:8000/v1/chat/completions` | Use your local model name |

If your provider only gives you a `base_url` ending in `/v1`, you can enter that too. The app will append `/chat/completions` automatically. Real API keys are saved in local `user_settings.json`, which is ignored by Git.

You can also use Google Cloud Translation:
```json
"translation": {
  "provider": "google",
  "api_key": "YOUR_GOOGLE_CLOUD_TRANSLATION_API_KEY",
  "source_lang": "en",
  "target_lang": "zh"
}
```

The Google option uses the official **Cloud Translation API Basic v2**, not a generic Google API. Enable Cloud Translation API in your Google Cloud project, then create an API Key. In Google mode, the model name and compatible endpoint are not used; the settings dialog disables those fields.

Google Cloud Translation pricing and free quota are controlled by Google: <https://cloud.google.com/translate/pricing>

### 4. Select an Audio Device
The app is designed to capture the audio that Windows is playing through your speakers, headphones, HDMI output, USB sound card, or virtual cable.

In the overlay settings, prefer devices labeled `[System Audio]` or `Loopback`, especially the one matching your current Windows playback device. Do not choose a normal microphone unless you intentionally want room audio; microphones usually cannot capture game voice playback directly.

If you only see microphones:
```bash
pip install PyAudioWPatch==0.2.12.8
```

You can also use VB-Cable as a fallback:
1. Download: <https://vb-audio.com/Cable/>
2. Set Windows default playback output to VB-Cable.
3. Select the matching VB-Cable capture/loopback device in the overlay.

NVIDIA GPU users can also try NVIDIA Broadcast / RTX Voice as a speech denoising and virtual-audio fallback:
1. Download NVIDIA Broadcast: <https://www.nvidia.com/en-us/geforce/broadcasting/broadcast-app/>
2. In NVIDIA Broadcast / RTX Voice, select the real microphone or speaker and enable the denoising effects you need.
3. If this app lists an NVIDIA Broadcast / RTX Voice virtual microphone or speaker, select it and test.

Note: NVIDIA Broadcast / RTX Voice is best for voice-chat denoising and virtual microphone/speaker workflows. For full game/system playback capture, prefer `[System Audio]` / `Loopback`, or use VB-Cable.

### 5. Start the App
Double-click `run.bat`, or run:
```bash
python main.py
```

Before joining a game or voice channel, use the gear settings to confirm both "Test Translation" and "Test Audio" pass. If you get stuck, click "Submit Feedback" in settings and paste the generated diagnostic template into a GitHub Issue.

### 6. Recommended Competitive Game Settings
For PUBG, APEX, Valorant, and similar real-time competitive games, prioritize frame time and response speed:

- Response Mode: `Fast / Game Performance`
- Recognition Device: `CPU`
- English Fast Path: enable Pure English environment only when teammate voice is almost entirely English

`Fast + Pure English` uses the English-only `base.en` model, which is usually faster than the multilingual `base` model for English game voice. The first enable downloads `base.en` on demand; even the Full package does not pre-bundle it. Keep Pure English off when the audio often contains Chinese or mixed-language speech, so the multilingual model can keep language detection active.

For developer performance benchmarks, skip the real audio device and inject a fixed file into the recognition pipeline with a 4-second speech + 3-second gap loop:
```bash
python main.py --benchmark-audio tests/assets/pubg_voice_30s.m4a
```

Optional knobs: `--benchmark-speech-seconds 4`, `--benchmark-gap-seconds 3`, and `--benchmark-duration-seconds 300`. WAV works directly; M4A/AAC requires PyAV, which is normally available through the faster-whisper install.

## Usage

### Overlay Controls
- **Ctrl+Shift+T**: Show/hide overlay
- **Ctrl+Alt+C**: Clear translation history
- **Ctrl+Alt+S**: Pause/resume translation
- **Drag overlay**: Move the overlay window
- **Gear button**: Configure translation provider, test API Key, test audio device, enable debug mode, submit feedback, and adjust opacity, colors, and hotkeys

### Translation Direction
Choose the fixed recognition and translation direction directly in the overlay title bar:
- The left dropdown is the recognition language.
- The right dropdown is the translation target language.
- The middle button swaps the direction.
- Officially supported directions are English → Chinese and Chinese → English.
- Mixed Chinese/English terms are preserved where possible, but the recognition and translation direction follows the selected dropdowns.
- Other languages are not exposed as selectable languages yet. Even when a provider supports more languages, VoxGo's current recognition and translation flow is built for English-Chinese use.

### Status And Error Messages
Important user-facing messages are shown in the overlay, including:
- Startup progress and Whisper model loading
- Whisper model name, download source, downloaded size, total size, and percentage during the lite package's first model download
- Selected system-audio / Loopback device
- Audio capture startup or device enumeration errors
- Pause/resume, clear history, and hotkey events
- Translation API timeout, provider HTTP status code, and provider error message

### Debug And Feedback
The settings dialog can enable debug mode. The app writes the latest speech-detected, recognition, translation, and overlay-update latency to `app.log`. The "Submit Feedback" button generates a diagnostic template with version, Windows build, audio device, translation provider, latest latency, and log paths.

### Mobile View
1. Keep your PC and phone on the same LAN.
2. Open `http://PC_IP:8765/mobile` on your phone.
3. The phone receives translation results in real time.

## Configuration
Edit `config.json` or use the overlay settings:

| Key | Description |
|-----|-------------|
| `app.setup_completed` | Whether the first-run wizard has been completed; saved to `user_settings.json` after setup |
| `debug.enabled` | Whether debug mode records the latest end-to-end latency |
| `whisper.model_size` | Whisper model size: tiny/base/small/medium |
| `whisper.fast_model_size` | Multilingual model used by Fast / Game Performance, default `base` |
| `whisper.pure_english_environment` | Pure English environment switch; uses an English-only model for faster English voice, useful for mostly-English PUBG/APEX/Valorant comms |
| `whisper.fast_english_model_size` | English-only model used by Fast + Pure English, default `base.en`; downloaded on first use |
| `whisper.device` | Recognition device, default `cpu` for Game Performance. Users can manually choose `cuda` for NVIDIA GPU / CUDA mode, or `auto` for GPU-first fallback behavior |
| `whisper.compute_type` | Compute precision, default `int8` on CPU. In CUDA mode, `auto` tries float16, int8_float16, then float32 before falling back to CPU; use int8_float16 as an experiment rather than the default |
| `whisper.auto_cpu_threads` | Whether to choose recognition thread count from CPU cores automatically, disabled by default for Game Performance; when disabled, VoxGo uses `whisper.cpu_threads` |
| `whisper.cpu_threads` | CPU load/recognition threads, default 2; keeping this small is more stable after a first-run model download |
| `whisper.num_workers` | Whisper worker count, default 1; increasing it uses more memory |
| `whisper.model_download_source` | First-run Whisper model download source for lite packages: `modelscope` for ModelScope China source (default and recommended for mainland China), `huggingface` for the official Hugging Face Hub, or `custom_hf_endpoint` for a custom Hugging Face Endpoint |
| `whisper.model_download_endpoint` | Hugging Face-compatible endpoint used only when `model_download_source` is `custom_hf_endpoint`; ModelScope is not a Hugging Face endpoint and should not be entered here |
| `whisper.language` | Fixed recognition language, synchronized with the left title-bar language dropdown; currently `en` / `zh` |
| `whisper.prompt_profile` | Recognition prompt profile, default `none` to avoid Whisper hallucinating the prompt; optionally use `general` or `game` manually |
| `whisper.vad_filter` | faster-whisper internal VAD, disabled by default to avoid double-cutting speech |
| `overlay.text_color` | Overlay text color |
| `overlay.bg_color` | Overlay background color, default dark gray `#20242A` |
| `overlay.bg_opacity` | Overlay background opacity, default 0.82 and adjustable in settings |
| `audio.latency_mode` | Response mode: `fast` (default Game Performance), `balanced`, `accurate`, or `custom`; also available from the gear settings |
| `audio.sample_rate` | Audio sample rate |
| `audio.chunk_duration_ms` | Audio block length in custom mode, balanced default 200ms; smaller is faster but can split speech more aggressively |
| `audio.silence_threshold` | Static fallback speech threshold in dBFS; default -40, avoid values above -20 for real voice chat |
| `audio.speech_threshold_blocks` | Consecutive speech blocks required before speech starts in custom mode, balanced default 2 |
| `audio.silence_limit_blocks` | Consecutive silent blocks required before segment flush in custom mode, balanced default 3 |
| `audio.speech_idle_timeout_ms` | Active segment flush when speech is buffered but no new audio frames arrive, balanced default 450ms |
| `audio.pre_roll_ms` | Audio kept before speech triggers, balanced default 450ms |
| `audio.soft_silence_margin_db` | Treat the tail as silence after it drops this many dB below the segment peak, default 10 |
| `audio.soft_silence_gate_margin_db` | Treat audio close to the speech gate as tail silence, default 5 |
| `audio.noise_calibration_seconds` | Seconds of startup background-audio calibration, default 2 |
| `audio.noise_margin_db` | Dynamic threshold margin above the measured noise floor, default 7 dB |
| `audio.max_speech_seconds` | Maximum seconds before forced splitting during continuous sound, balanced default 4.5s |
| `audio.min_segment_seconds` | Drop segments before recognition when active voice is shorter than this, balanced default 0.35s; set 0 to disable |
| `audio.audio_queue_max_blocks` | Raw audio queue limit, default 5; old audio is dropped when full to avoid buildup while paused or busy |
| `audio.min_segment_peak_margin_db` | Require the segment peak to exceed the current speech gate by this many dB before recognition, balanced default 1.5; set 0 to disable |
| `translation.provider` | Translation provider: `openai_compatible` or `google` |
| `translation.api_key` | API Key for the selected provider; use a Google Cloud Translation API Key in Google mode |
| `translation.model` | OpenAI-compatible model name, default `tencent/Hunyuan-MT-7B`; unused in Google mode |
| `translation.endpoint` | OpenAI-compatible endpoint or `/v1` base URL; unused in Google mode |
| `translation.max_tokens` | Maximum translation output length, default 80 to avoid expansion |
| `translation.temperature` | Translation randomness, default 0 for faithful and stable subtitles |
| `translation.source_lang` | Fixed recognition language saved from the left title-bar dropdown; currently `en` / `zh` |
| `translation.target_lang` | Fixed translation target saved from the right title-bar dropdown; currently `en` / `zh` |
| `translation.context_messages` | Translation history context count, default 0 to avoid stale context pollution and completion |
| `translation.timeout_seconds` | Single translation request timeout, default 12 seconds; increase it if your provider is slow |
| `translation.max_concurrent_requests` | Concurrent translation requests, default 2; lower is steadier, higher can make slow providers time out more easily |

## Troubleshooting

### Cannot Capture Audio
- Choose `[System Audio]` / `Loopback`, not a normal microphone.
- First click "Test Audio" in the wizard or gear settings, play game/Discord/video sound, and check whether the level bar moves.
- Run `python diagnostics/list_devices.py` and confirm that system-audio devices are visible.
- Make sure the game sound is playing through the same speaker/headphone device you selected.
- If you use Bluetooth, HDMI, or a USB sound card, choose the matching system-audio/loopback item.
- Re-run `install.bat` or install `PyAudioWPatch==0.2.12.8`.
- Try VB-Cable if your device driver does not expose loopback capture.
- NVIDIA GPU users can try NVIDIA Broadcast / RTX Voice virtual devices, but full game/system playback capture should still prefer `[System Audio]` / `Loopback`.
- Try running as administrator.

### Translation Fails
- Check the overlay message for API status code and provider error details.
- Use "Test API Key" in the wizard or gear settings to verify the Key, model, and endpoint before entering a game.
- Confirm API Key, model name, and endpoint in the gear settings.
- If using a local model, make sure the endpoint is reachable and compatible with Chat Completions.
- Increase `translation.timeout_seconds` if the provider is slow.

### Recognition Is Inaccurate
- Real voice chat is often quieter than normalized video audio; keep `audio.silence_threshold` around -40.
- Keep the room/game relatively quiet for the first 2 seconds so the app can calibrate the background noise floor.
- Increase `whisper.model_size`.
- Keep `whisper.prompt_profile=none` by default; if phrases from the prompt appear in the transcript, do not enable long Whisper prompts.
- Keep `whisper.vad_filter=false` if beginnings or endings of sentences are being clipped.
- Lower background music volume.
- Ensure the selected audio device is the one actually playing game voice.
- If accents, long sentences, livestreams, meetings, or slower games matter more than speed, choose Accurate response mode in the gear settings.

### Startup Says cublas64_12.dll Is Missing
- This means the CUDA/cuBLAS runtime is missing; it is not a translation API problem.
- Lite and Full do not bundle CUDA DLLs and do not download them at startup; Full-CUDA / GPU bundles them.
- When you select `NVIDIA GPU / CUDA`, VoxGo detects the GPU first. AMD/Intel GPUs are not supported for this CUDA path and will keep the previous device.
- On NVIDIA machines, Lite/Full can download the CUDA runtime on demand. Restart VoxGo after the download completes; if it fails, the app explains why and falls back to CPU.

### Lite Package Model Download Is Slow Or Fails
- The overlay shows the Whisper model, repository, download source, downloaded size, total size, and percentage.
- Download failures show the concrete network error and are also written to `app.log` and `crash_report.txt` in the app folder.
- The default source is ModelScope and downloads the required `Systran/faster-whisper-small` / `Systran/faster-whisper-base` files from `modelscope.cn`.
- Enabling Pure English downloads `Systran/faster-whisper-base.en` or the configured English-only model on demand.
- `hf-mirror.com` currently redirects back to `huggingface.co`, so it is unreliable when the user's network cannot reach Hugging Face. If you still want to try it, enter it only as a custom Hugging Face Endpoint.
- If ModelScope or a custom source still fails, switch to the official Hugging Face source and restart, or use the full package.
- The full package already includes the Whisper small and base multilingual models, so the default Game Performance profile does not need the first-run multilingual model download; English-only models still download on demand.

### Translation Latency Is High
- Enable debug mode in the gear settings, reproduce once, then use "Submit Feedback" to copy the latest latency data.
- The default real-user profile is Fast / Game Performance: CPU int8, 2 threads, one worker, one translation request, and a base-level performance model to protect frame time in PUBG, APEX, Valorant, and similar competitive games. GPU mode remains a manual high-performance hardware option, not the default game profile.
- If voice is almost entirely English, enable Pure English to use `base.en`, which is usually faster than multilingual `base`; the model downloads on first use.
- Check network connectivity and provider speed.
- Lower `whisper.model_size` to speed up recognition.
- Use a local translation model if you already have one deployed.

## Scope
This tool captures Windows system playback audio. It is not hard-coded for specific games and should not claim individual game compatibility without testing. If the game voice is audible through the selected playback device and Windows exposes a matching system-audio/loopback capture device, it can usually be tried.

Some games, anti-cheat systems, exclusive audio mode, remote streaming tools, DRM protection, or special sound drivers may block capture. Use another output device, disable exclusive mode, or route audio through VB-Cable when needed.

## Notes
1. Lite downloads the Whisper model on first use; Full and Full-CUDA include multilingual Whisper small and base, while English-only models download on demand.
2. Translation requires network access unless you use a local model.
3. Start this app before joining a game voice session.
4. Keep the mobile page open if you use mobile mirroring.

## Mobile Troubleshooting
- Allow port `8765` through Windows Firewall.
- Keep the phone and PC on the same LAN.
- If the phone shows 502, first open `http://127.0.0.1:8765/mobile` on the PC. If that works, check the phone URL, proxy, or firewall.
- Use the URL shown by the overlay QR code/startup notice, not a browser proxy address.

## License
This community edition is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE).

Closed-source commercial use, private custom distribution, or commercial edition licensing requires separate authorization.
