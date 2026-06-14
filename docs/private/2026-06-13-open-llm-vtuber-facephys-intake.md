# External repo/social intake evidence — Open-LLM-VTuber + FacePhys

Date: 2026-06-13

## Source A — GitHub repo

- URL: https://github.com/Open-LLM-VTuber/Open-LLM-VTuber
- Repo facts via GitHub API: Python; default branch `main`; description: "Talk to any LLM with hands-free voice interaction, voice interruption, and Live2D taking face running locally across platforms"; 11k+ stars / 1.2k+ forks at intake.
- README signals: voice-interactive AI companion; real-time voice conversations; visual perception; Live2D avatar; local/offline mode; web + desktop client; desktop-pet mode; multi-backend LLM/ASR/TTS/VAD.
- Architecture signals from `CLAUDE.md`: FastAPI WebSocket server; per-connection service context; WebSocket handler routes audio/conversation/Live2D messages; factory-pattern engines for Agent/ASR/TTS/VAD; config manager; conversation handlers; MCP system under `src/open_llm_vtuber/mcpp/`; frontend submodule; Live2D models; character configs; chat history/cache.
- Top-level structure observed: `src/`, `frontend`, `run_server.py`, `config_templates/`, `characters/`, `prompts/`, `doc/`, `mcp_servers.json`, `CLAUDE.md`, `pyproject.toml`, `uv.lock`, `pixi.lock`.

Interpretation for Hermes:
- Treat as local-brain / voice-console / visual-avatar interaction reference, not provider-quota work.
- Useful patterns: low-latency interruptible voice loop, per-session service context, configurable multi-engine adapters, Live2D/avatar projection, MCP tool registry in a conversational avatar runtime.
- First task should be source-review + gap mapping + minimal reversible adapter/prototype boundary, not installation or daemon start.

## Source B — WeChat Channels social lead

- URL: https://weixin.qq.com/sph/Ap7f2sP55m
- Author: 小牛聊AI
- Date visible on page: 2026年6月13日
- Visible text: “微面科技获顺为资本数百万美元 0.2M小模型跑在手机摄像头……FacePhys基座模型，通过普通摄像头就能无接触测量心率、呼吸、情绪等120多项指标，精度达到医疗级，心率误差不超过2BPM……0.2M参数，可以在手机摄像头里实时运行，延迟不到10毫秒……合作伙伴包括海尔机器人。”
- Engagement visible: likes 192, shares 986, favorites/hearts 81, comments 18.
- Hashtags: #人工智能 #生理感知 #FacePhys #AI情绪识别 #端侧模型 #人机交互 #医疗级检测 #实时推理

Canonical mapping signals:
- GitHub Search `FacePhys` found `FacePhys/FacePhys` described as “Official Code Repo of FacePhys” and README exposes public SDK examples for FacePhys video detection API: JavaScript/Python/Java SDKs, presigned upload, object storage upload, physiological detection, grouped results including heart rate, HRV, blood pressure, SpO2, emotion, behavior, appearance, billing fields; docs warn not to expose long-lived secrets in public frontend code.
- GitHub Search also found `KegangWangCCNU/FacePhys-Release` described as an rPPG algorithm using State Space Models and LiteRT optimized for on-device CPU deployment, plus `KegangWangCCNU/FacePhys-Demo` browser PWA demo using local LiteRT/WebAssembly inference for webcam rPPG with privacy/offline claims.

Interpretation for Hermes:
- Treat WeChat content as a lead, not proof. Claims about 0.2M parameters / medical-grade / <10ms / 120+ indicators need source verification from FacePhys docs/papers/company materials before product use.
- First task should map FacePhys/contactless physiological perception into Hermes visual-conversation / external-control safety boundaries: privacy, consent, camera permission, medical-claim risk, local vs cloud SDK boundary, and possible read-only perception adapter contract.
- No camera access, SDK credentials, medical inference, or daemon install during intake.
