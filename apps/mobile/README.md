# Arevik AI — Flutter MVP, first iteration

Implemented source: push-to-talk English ↔ Armenian, voice recording, POST /api/v1/translate/file, transcript, translated text, replayable WAV audio, language swap, loading and error states, configurable API base URL.

This is **not yet** a two-person live interpreter or a tested mobile release.

## Build requirements

Install Flutter stable and Android SDK on your development workstation.
This repository does not yet include generated Android/iOS runner directories.

```bash
cd apps/mobile
flutter create --platforms=android,ios --project-name arevik_mobile .
flutter pub get
flutter test
flutter run --dart-define=AREVIK_API_URL=http://10.0.2.2:8000
```

Add `android.permission.RECORD_AUDIO` to android/app/src/main/AndroidManifest.xml.
iOS requires `NSMicrophoneUsageDescription` in Info.plist.
For Android emulator use local port forwarding through SSH to your EC2 loopback
API; 10.0.2.2 is the emulator's host gateway. Android debug HTTP requires a
debug-only cleartext network policy. Do not permit cleartext in release.

For physical devices use an **authenticated HTTPS** endpoint. The EC2 API is
currently loopback-bound, not accessible directly from a phone. Do not open the
unauthenticated server port publicly.

## Remaining MVP work

- Secure HTTPS gateway, per-session authorization and request limits.
- Create/join two-person sessions and WebSocket media transport.
- VAD, utterance turn-taking, headset audio routing and reconnect behavior.
- Integrate CT2 quality translation, Eastern Armenian SpeechT5, and Persian.
- Validate Flutter build on Android and iOS and run real-device end-to-end tests.
