# Arevik V1 architecture

## Product contract

Arevik V1 enables two people who do not share a language to hold a face-to-face conversation. Each participant uses their own phone and headset.

The technical architecture must optimize for:

1. low perceived translation latency,
2. CPU-first self-hosted inference,
3. privacy by default,
4. a very small operational surface,
5. replaceable AI components.

## Target realtime flow

```text
Phone A microphone
  → WebSocket
  → VAD / utterance segmentation
  → STT
  → translation
  → TTS
  → WebSocket
  → Phone B headset

Phone B follows the same path in reverse.
```

## V1 language pair

- English: `en`
- Armenian: `hy`

The service code is language-pair aware rather than hard-coded to function names such as `translate_english_to_armenian`. New language pairs should be added by configuration and adapters.

## Phase plan

### Phase 1 — local file pipeline
Prove `audio → text → translation → audio` on the target AWS CPU class and record latency per stage.

### Phase 2 — realtime backend
Add session pairing, WebSocket audio transport, VAD, turn control, and translated audio delivery.

### Phase 3 — Flutter app
Build iOS + Android from one product codebase, with native audio-routing bridges where required.

### Phase 4 — headset reliability
Harden iOS AVAudioSession / AVAudioEngine and Android AudioManager / AudioRecord / AudioTrack behavior.

### Phase 5 — website
Ship the public marketing site separately from the translator runtime.

## Current local model choices

### STT
`faster-whisper`, CPU INT8, multilingual Whisper Small by default.

### Translation
Helsinki-NLP OPUS-MT:
- `Helsinki-NLP/opus-mt-en-hy`
- `Helsinki-NLP/opus-mt-hy-en`

### TTS
eSpeak NG is the functional baseline for Phase 1. It is not the intended final voice quality. The TTS interface will later benchmark Armenian SpeechT5/ONNX and, only if necessary, an external provider fallback.

## Non-goals for the first prototype

No authentication, database, payment, user history, analytics dashboard, profile system, avatars, curriculum, 3D world, or general AI chat.
