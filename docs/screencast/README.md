# Wizard screencast

[Download the videos](https://github.com/coffeerv/dotfiles-public/releases/tag/tutorial-2026-10-19) · [Español](../../README.es.md)

The 4:43 tutorial demonstrates a personal GitHub identity and two fictional organizations in an isolated Linux container. It includes Spanish (Mexico) and English narration, generated with Gemini TTS on Vertex AI, and selectable subtitles. No real accounts, vaults, pushes, or signatures were exercised.

Release assets:

- `dotfiles-bilingual.mp4`: both audio tracks and subtitle languages; Spanish audio is the default.
- `dotfiles-es.mp4`: Spanish audio and subtitles.
- `dotfiles-en.mp4`: English audio and subtitles.

The recorded source revision is `c053576095709078be94fed6e31a07b6ae42d178`. This is a documentation release, not a new installer version.

## Production sources

- [Spanish script](scripts/narration-es.txt) and [English script](scripts/narration-en.txt); [narration.json](scripts/narration.json) is the generation source of truth.
- [Spanish subtitles](subtitles/es.srt) and [English subtitles](subtitles/en.srt), aligned to the published video.
- [Dockerfile](Dockerfile) for preparing an isolated demo environment.
- `scripts/generate-vertex.py`: speech generation authenticated with `gcloud`.
- `scripts/verify-voice.py`: local Whisper transcription and script comparison.
- `scripts/edit.py`: title cards and chapter assembly.
- `scripts/align-subtitles.py`: align script words using local transcription timestamps.
- `scripts/build-final.py`: render, normalize audio, align subtitles, and export the three videos.

Large media, intermediate files, credentials, and local production metadata are excluded from Git. The raw recording is not distributed. **A fresh clone cannot reproduce the published edit without the original capture.** The cut points in `edit.py` refer to that capture; update them when recording a new take. TTS output is nondeterministic, so a new generation can change timing and delivery.

## Prepare an isolated recording

From the repository root, with Docker installed:

```sh
mkdir -p docs/screencast/build/container
git archive HEAD -o docs/screencast/build/container/repo.tar
cp docs/screencast/Dockerfile docs/screencast/build/container/Dockerfile
docker build -t dotfiles-screencast docs/screencast/build/container
docker run --name dotfiles-screencast-demo --hostname demo -it dotfiles-screencast
```

Inside the container:

```sh
chezmoi --source /home/demo/dotfiles init
mise run setup -- --advanced
```

Use fictional identities and demo public keys. Do not mount your home directory or connect a real password manager. The original capture used GUI interaction through Orca and FFmpeg screen capture. Keep only the demo terminal in the capture region. Stop the container after recording. Tool versions in this convenience Dockerfile are not pinned, so a future wizard/tool combination may differ.

## Generate narration and rebuild

Prerequisites: Python 3.10+, FFmpeg/ffprobe with libx264, Google Cloud CLI, and an authenticated account with permission to invoke the TTS model in a billing-enabled project with the Vertex AI API enabled. The local transcription step uses MLX Whisper on Apple Silicon macOS. Rendering uses Helvetica/Menlo on macOS or DejaVu fonts on Linux; other platforms can set explicit font paths.

Install production dependencies in an isolated virtual environment:

```sh
python3 -m venv docs/screencast/build/venv
. docs/screencast/build/venv/bin/activate
python3 -m pip install Pillow mlx-whisper
```

Then, from the repository root:

```sh
# Required: choose the project that should pay for speech generation.
export GOOGLE_CLOUD_PROJECT=your-project-id
# Optional overrides; these are the defaults.
export SCREENCAST_WORKDIR="$PWD/docs/screencast/build"
export TTS_MODEL=gemini-3.8-flash-tts
export TTS_VOICE=Kore

mkdir -p "$SCREENCAST_WORKDIR/video"
cp /path/to/original-capture.mp4 "$SCREENCAST_WORKDIR/video/wizard-raw.mp4"
python3 docs/screencast/scripts/generate-vertex.py
python3 docs/screencast/scripts/verify-voice.py
python3 docs/screencast/scripts/build-final.py
```

Generation incurs Google Cloud charges. Tokens are obtained from `gcloud` in memory, never saved in the repo. Existing narration WAVs are reused: choose a fresh work directory when changing scripts, voice, or model. If Python cannot find your system certificates, set `SSL_CERT_FILE` to your trusted CA bundle; do not disable certificate verification.

Optional overrides: `WHISPER_MODEL`, `SCREENCAST_FONT`, and `SCREENCAST_MONO_FONT`. Whisper may download its model on the first run. Set `HF_HUB_OFFLINE=1` only after caching it. Before publishing, review transcription differences, listen to both languages, check subtitle timing, and inspect the final video. Automated transcript matching does not replace listening review.

Outputs are written under `SCREENCAST_WORKDIR`. Copy the final SRT files back into `docs/screencast/subtitles/` only when updating the published release. Upload the MP4 files as release assets rather than committing them.

API reference: [Google Cloud Gemini TTS](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/text-to-speech/overview).
