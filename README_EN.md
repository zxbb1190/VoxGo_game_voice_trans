# Game Voice Translator

Chinese documentation: [README.md](README.md)

An open-source real-time voice translation overlay for PC gamers, designed for overseas servers, guild voice chat, Discord teammates, and live-stream subtitle assistance.

## Features
- **System-audio capture**: Captures Windows playback audio through WASAPI Loopback, not the microphone.
- **Local speech recognition**: Uses faster-whisper for offline speech-to-text with a fixed Chinese or English recognition language.
- **Fixed translation direction**: Choose the recognition language and translation target from the overlay title bar, with one-click swap.
- **OpenAI-compatible APIs**: Works with Chat Completions-compatible providers such as SiliconFlow, DeepSeek, Qwen, GLM, OpenAI-compatible gateways, and local models.
- **In-game overlay**: Transparent always-on-top PyQt overlay for translation results.
- **Visible status and error messages**: Startup status, selected audio device, pause/resume events, API status codes, and provider error messages are shown in the overlay.
- **Mobile mirror**: Pushes translations to a browser on the same LAN through WebSocket.
- **Global hotkeys**: Toggle overlay, clear history, and pause/resume translation.

## Project Layout
```text
game_voice_translator/
├── main.py               # Main application
├── audio_capture.py      # Windows system-audio capture
├── speech_recognition.py # faster-whisper speech recognition
├── translator.py         # OpenAI-compatible translation client
├── overlay.py            # PyQt5 overlay window
├── mobile_server.py      # Mobile WebSocket server
├── config.example.json   # Configuration template
├── config.json           # Local config, ignored by Git
├── requirements.txt      # Python dependencies
├── install.bat           # Windows installer script
├── run.bat               # Windows launcher
├── README.md             # Chinese documentation
└── README_EN.md          # English documentation
```

## Quick Start

### 1. Install Dependencies
Double-click `install.bat`, or run:
```bash
pip install -r requirements.txt
```

### 2. Configure Translation API
Copy the example config first:
```bat
copy config.example.json config.json
```

Then edit `config.json`, or start the app and use the gear button in the overlay to configure API Key, model name, and compatible endpoint:
```json
"translation": {
  "api_key": "YOUR_OPENAI_COMPATIBLE_API_KEY",
  "model": "tencent/Hunyuan-MT-7B",
  "endpoint": "https://api.siliconflow.cn/v1/chat/completions"
}
```

The default template uses SiliconFlow with `tencent/Hunyuan-MT-7B`, a free translation model. Register and create an API Key to use it. Availability and quota are subject to the provider's current policy.

Register/get API Key: <https://cloud.siliconflow.cn/i/iA6DF2nP>

Common OpenAI-compatible examples:

| Provider | Compatible endpoint example | Model example |
|----------|-----------------------------|---------------|
| SiliconFlow | `https://api.siliconflow.cn/v1/chat/completions` | `tencent/Hunyuan-MT-7B` |
| DeepSeek | `https://api.deepseek.com/chat/completions` | `deepseek-v4-flash` |
| Qwen / Alibaba Model Studio | `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` | `qwen-plus` |
| GLM / Zhipu | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | `glm-4.7` |
| Local model | `http://127.0.0.1:11434/v1/chat/completions` or `http://127.0.0.1:8000/v1/chat/completions` | Use your local model name |

If your provider only gives you a `base_url` ending in `/v1`, you can enter that too. The app will append `/chat/completions` automatically. Real API keys are saved in local `user_settings.json`, which is ignored by Git.

### 3. Select an Audio Device
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

### 4. Start the App
Double-click `run.bat`, or run:
```bash
python main.py
```

## Usage

### Overlay Controls
- **Ctrl+Shift+T**: Show/hide overlay
- **Ctrl+Alt+C**: Clear translation history
- **Ctrl+Alt+S**: Pause/resume translation
- **Drag overlay**: Move the overlay window
- **Gear button**: Configure API Key, model name, endpoint, audio device, opacity, colors, and hotkeys

### Translation Direction
Choose the fixed recognition and translation direction directly in the overlay title bar:
- The left dropdown is the recognition language.
- The right dropdown is the translation target language.
- The middle button swaps the direction.
- Mixed Chinese/English terms are preserved where possible, but the recognition and translation direction follows the selected dropdowns.

### Status And Error Messages
Important user-facing messages are shown in the overlay, including:
- Startup progress and Whisper model loading
- Selected system-audio / Loopback device
- Audio capture startup or device enumeration errors
- Pause/resume, clear history, and hotkey events
- Translation API timeout, provider HTTP status code, and provider error message

### Mobile View
1. Keep your PC and phone on the same LAN.
2. Open `http://PC_IP:8765/mobile` on your phone.
3. The phone receives translation results in real time.

## Configuration
Edit `config.json` or use the overlay settings:

| Key | Description |
|-----|-------------|
| `whisper.model_size` | Whisper model size: tiny/base/small/medium |
| `whisper.device` | Recognition device, default `cpu`; users can change it from the gear settings under Recognition Device. Use `auto` or `cuda` only after installing a matching NVIDIA CUDA runtime |
| `whisper.compute_type` | Compute precision, default `auto`: int8 on CPU, float16 on CUDA |
| `whisper.language` | Fixed recognition language, synchronized with the left title-bar language dropdown |
| `whisper.prompt_profile` | Recognition prompt profile, default `none` to avoid Whisper hallucinating the prompt; optionally use `general` or `game` manually |
| `whisper.vad_filter` | faster-whisper internal VAD, disabled by default to avoid double-cutting speech |
| `overlay.text_color` | Overlay text color |
| `overlay.bg_color` | Overlay background color, default dark gray `#20242A` |
| `overlay.bg_opacity` | Overlay background opacity, default 0.82 and adjustable in settings |
| `audio.sample_rate` | Audio sample rate |
| `audio.silence_threshold` | Static fallback speech threshold in dBFS; default -40, avoid values above -20 for real voice chat |
| `audio.speech_idle_timeout_ms` | Active segment flush when speech is buffered but no new audio frames arrive, default 900ms |
| `audio.soft_silence_margin_db` | Treat the tail as silence after it drops this many dB below the segment peak, default 10 |
| `audio.soft_silence_gate_margin_db` | Treat audio close to the speech gate as tail silence, default 5 |
| `audio.noise_calibration_seconds` | Seconds of startup background-audio calibration, default 2 |
| `audio.noise_margin_db` | Dynamic threshold margin above the measured noise floor, default 7 dB |
| `audio.max_speech_seconds` | Maximum seconds before forced splitting during continuous sound, recommended 6-10 |
| `translation.api_key` | OpenAI-compatible API Key |
| `translation.model` | Model name, default `tencent/Hunyuan-MT-7B` |
| `translation.endpoint` | Compatible endpoint or `/v1` base URL |
| `translation.max_tokens` | Maximum translation output length, default 80 to avoid expansion |
| `translation.temperature` | Translation randomness, default 0 for faithful and stable subtitles |
| `translation.source_lang` | Fixed recognition language saved from the left title-bar dropdown |
| `translation.target_lang` | Fixed translation target saved from the right title-bar dropdown |
| `translation.context_messages` | Translation history context count, default 0 to avoid stale context pollution and completion |

## Troubleshooting

### Cannot Capture Audio
- Choose `[System Audio]` / `Loopback`, not a normal microphone.
- Run `python list_devices.py` and confirm that system-audio devices are visible.
- Make sure the game sound is playing through the same speaker/headphone device you selected.
- If you use Bluetooth, HDMI, or a USB sound card, choose the matching system-audio/loopback item.
- Re-run `install.bat` or install `PyAudioWPatch==0.2.12.8`.
- Try VB-Cable if your device driver does not expose loopback capture.
- NVIDIA GPU users can try NVIDIA Broadcast / RTX Voice virtual devices, but full game/system playback capture should still prefer `[System Audio]` / `Loopback`.
- Try running as administrator.

### Translation Fails
- Check the overlay message for API status code and provider error details.
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

### Startup Says cublas64_12.dll Is Missing
- This means the CUDA/cuBLAS runtime is missing; it is not a translation API problem.
- The default configuration uses CPU recognition and does not require CUDA.
- In the gear settings, change Recognition Device to `CPU (Recommended)`, then restart the app.
- Use `cuda` only on an NVIDIA GPU machine with a matching CUDA 12 and cuDNN runtime for faster-whisper/ctranslate2.

## Scope
This tool captures Windows system playback audio. It is not hard-coded for specific games and should not claim individual game compatibility without testing. If the game voice is audible through the selected playback device and Windows exposes a matching system-audio/loopback capture device, it can usually be tried.

Some games, anti-cheat systems, exclusive audio mode, remote streaming tools, DRM protection, or special sound drivers may block capture. Use another output device, disable exclusive mode, or route audio through VB-Cable when needed.

## Notes
1. The first run may download the Whisper model.
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
