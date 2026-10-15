import 'dart:convert';
import 'dart:io';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

void main() => runApp(const ArevikApp());

class ArevikApp extends StatelessWidget {
  const ArevikApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Arevik AI',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(useMaterial3: true, colorSchemeSeed: const Color(0xFF5267B3),
      scaffoldBackgroundColor: const Color(0xFFF7F8FC)),
    home: const InterpreterScreen(),
  );
}

class InterpreterScreen extends StatefulWidget {
  const InterpreterScreen({super.key});
  @override
  State<InterpreterScreen> createState() => _InterpreterScreenState();
}

class _InterpreterScreenState extends State<InterpreterScreen> {
  final _recorder = AudioRecorder();
  final _player = AudioPlayer();
  final _server = TextEditingController(text: const String.fromEnvironment(
    'AREVIK_API_URL', defaultValue: 'https://api.arevikai.com'));
  final _email = TextEditingController();
  final _password = TextEditingController();
  String? _sessionToken;
  bool _authenticated = false;
  String source = 'en';
  String target = 'hy';
  String stage = 'Ready';
  String original = '';
  String translation = '';
  String? error;
  bool recording = false;
  bool processing = false;
  String? recordedPath;
  String? spokenFile;

  @override
  void dispose() {
    _server.dispose();
    _email.dispose();
    _password.dispose();
    _recorder.dispose();
    _player.dispose();
    super.dispose();
  }

  Future<void> _login({bool register = false}) async {
    if (processing) return;
    setState(() { processing = true; error = null; });
    try {
      final base = _server.text.trim().replaceAll(RegExp(r'/+
    if (processing || recording) return;
    try {
      if (!await _recorder.hasPermission()) {
        throw StateError('Microphone permission is required.');
      }
      final dir = await getTemporaryDirectory();
      final path = '${dir.path}/arevik-recording.wav';
      await _recorder.start(const RecordConfig(encoder: AudioEncoder.wav,
        sampleRate: 16000, numChannels: 1), path: path);
      if (!mounted) return;
      setState(() { recording = true; stage = 'Recording...'; error = null; });
    } catch (e) {
      if (mounted) setState(() { error = 'Unable to record: $e'; stage = 'Ready'; });
    }
  }

  Future<void> _stopAndTranslate() async {
    if (!recording) return;
    setState(() { recording = false; processing = true; stage = 'Recognizing & translating...'; error = null; });
    try {
      recordedPath = await _recorder.stop();
      final path = recordedPath;
      if (path == null || !File(path).existsSync()) throw StateError('Recording was not saved');
      final url = Uri.parse('${_server.text.trim().replaceAll(RegExp(r"/+$"), "")}/api/v1/translate/file');
      if (url.scheme != 'https' && !(url.host == '10.0.2.2' || url.host == '127.0.0.1' || url.host == 'localhost')) {
        throw StateError('Use HTTPS for remote servers.');
      }
      final request = http.MultipartRequest('POST', url);
      if (_sessionToken == null) throw StateError('Please sign in.');
      request.headers['Authorization'] = 'Bearer $_sessionToken';
      request.fields['source_language'] = source;
      request.fields['target_language'] = target;
      request.files.add(await http.MultipartFile.fromPath('file', path, filename: 'recording.wav'));
      final streamed = await request.send().timeout(const Duration(seconds: 90));
      final response = await http.Response.fromStream(streamed);
      if (response.statusCode != 200) throw StateError('Server ${response.statusCode}: ${response.body}');
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final bytes = base64Decode((payload['audio'] as Map<String,dynamic>)['data'] as String);
      final dir = await getTemporaryDirectory();
      spokenFile = '${dir.path}/arevik-translated.wav';
      await File(spokenFile!).writeAsBytes(bytes, flush: true);
      if (!mounted) return;
      setState(() {
        original = payload['source_text'] as String? ?? '';
        translation = payload['translated_text'] as String? ?? '';
        stage = 'Translated';
      });
      await _player.play(DeviceFileSource(spokenFile!));
    } catch (e) {
      if (mounted) setState(() { error = e.toString(); stage = 'Retry'; });
    } finally {
      final path = recordedPath;
      if (path != null) { try { await File(path).delete(); } catch (_) {} }
      if (mounted) setState(() => processing = false);
    }
  }

  void _swap() {
    if (recording || processing) return;
    setState(() { final old = source; source = target; target = old; });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Arevik AI'), centerTitle: false,
      backgroundColor: Colors.transparent),
    body: SafeArea(child: ListView(padding: const EdgeInsets.all(20), children: [
      if (!_authenticated) ...[
        const Text('Sign in to Arevik', style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold)),
        const SizedBox(height: 15),
        TextField(controller: _email, decoration: const InputDecoration(labelText: 'Email', border: OutlineInputBorder())),
        const SizedBox(height: 10),
        TextField(controller: _password, obscureText: true, decoration: const InputDecoration(labelText: 'Password (12+ characters)', border: OutlineInputBorder())),
        const SizedBox(height: 10),
        TextField(controller: _server, decoration: const InputDecoration(labelText: 'HTTPS API URL', border: OutlineInputBorder())),
        const SizedBox(height: 10),
        FilledButton(onPressed: processing ? null : () => _login(), child: const Text('Sign in')),
        OutlinedButton(onPressed: processing ? null : () => _login(register: true), child: const Text('Create account')),
        if (error != null) SelectableText(error!, style: const TextStyle(color: Colors.red)),
      ] else ...[
      Align(alignment: Alignment.centerRight, child: TextButton(onPressed: _logout, child: const Text('Sign out'))),
      const Text('Understand each other.', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
      const SizedBox(height: 5),
      const Text('Early MVP • Push-to-talk translation', style: TextStyle(color: Colors.black54)),
      const SizedBox(height: 25),
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(children: [
        const Align(alignment: Alignment.centerLeft,
          child: Text('Language direction', style: TextStyle(fontWeight: FontWeight.bold))),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(child: _languagePicker(source, (v) => setState(() { source=v; if (source == target) target = v == 'en' ? 'hy':'en'; }))),
          IconButton(onPressed: recording || processing ? null : _swap, icon: const Icon(Icons.swap_horiz)),
          Expanded(child: _languagePicker(target, (v) => setState(() { target=v; if (source == target) source = v == 'en' ? 'hy':'en'; }))),
        ]),
      ]))),
      const SizedBox(height: 16),
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
        crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Connection', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          TextField(controller: _server, enabled: !recording && !processing,
            decoration: const InputDecoration(labelText: 'API base URL',
              hintText: 'https://your-server.example', border: OutlineInputBorder()),
            keyboardType: TextInputType.url),
          const SizedBox(height: 8),
          const Text('Authenticated session is active.'),
          const SizedBox(height: 8),
          const Text('For Android emulator use 10.0.2.2 with an SSH tunnel. '
            'Real phones require an authenticated HTTPS endpoint.',
            style: TextStyle(fontSize: 12, color: Colors.black54)),
        ]))),
      const SizedBox(height: 22),
      Center(child: Text(stage, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600))),
      const SizedBox(height: 14),
      Center(child: SizedBox(width: 112, height: 112, child: FilledButton(
        onPressed: processing ? null : recording ? _stopAndTranslate : _start,
        style: FilledButton.styleFrom(shape: const CircleBorder(),
          backgroundColor: recording ? Colors.redAccent : null),
        child: Icon(recording ? Icons.stop : Icons.mic, size: 46),
      ))),
      const SizedBox(height: 10),
      Center(child: Text(recording ? 'Tap to stop & translate' : 'Tap to speak')),
      if (processing) const Padding(padding: EdgeInsets.only(top: 12),
        child: LinearProgressIndicator()),
      if (error != null) Padding(padding: const EdgeInsets.only(top: 16),
        child: SelectableText(error!, style: const TextStyle(color: Colors.red))),
      const SizedBox(height: 24),
      _resultCard('You said', original.isEmpty ? 'Your speech transcript appears here' : original),
      const SizedBox(height: 12),
      _resultCard('Translation', translation.isEmpty ? 'Translation appears here' : translation),
      const SizedBox(height: 16),
      OutlinedButton.icon(
        onPressed: spokenFile == null ? null : () => _player.play(DeviceFileSource(spokenFile!)),
        icon: const Icon(Icons.volume_up), label: const Text('Replay translation')),
      const SizedBox(height: 15),
      const Text('Paired sessions and live streaming are being integrated. '
        'Speech translation supports English, Armenian and Persian after backend deployment.',
        style: TextStyle(color: Colors.black54, fontSize: 12)),
      ],
    ])),
  );

  Widget _languagePicker(String value, ValueChanged<String> onChanged) =>
    DropdownButtonFormField<String>(value: value,
      decoration: const InputDecoration(border: OutlineInputBorder()),
      items: const [
        DropdownMenuItem(value: 'en', child: Text('English')),
        DropdownMenuItem(value: 'hy', child: Text('Armenian')),
        DropdownMenuItem(value: 'fa', child: Text('Persian')),
      ], onChanged: recording || processing ? null : onChanged);

  Widget _resultCard(String title, String body) =>
    Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(fontSize: 13, color: Colors.black54)),
        const SizedBox(height: 8),
        SelectableText(body, style: const TextStyle(fontSize: 18)),
      ])));
}
), '');
      final uri = Uri.parse('$base/api/v1/auth/${register ? 'register' : 'login'}');
      if (uri.scheme != 'https' && uri.host != '10.0.2.2' && uri.host != 'localhost') {
        throw StateError('HTTPS is required.');
      }
      final res = await http.post(uri, headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': _email.text.trim(), 'password': _password.text}))
          .timeout(const Duration(seconds: 30));
      if (res.statusCode != 200) throw StateError('Authentication failed: ${res.statusCode}');
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (!mounted) return;
      setState(() { _sessionToken = data['access_token'] as String; _authenticated = true; stage = 'Ready'; });
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => processing = false);
    }
  }

  Future<void> _logout() async {
    final token = _sessionToken;
    _sessionToken = null;
    if (mounted) setState(() { _authenticated = false; original = ''; translation = ''; });
    if (token == null) return;
    try {
      await http.post(Uri.parse('${_server.text.trim().replaceAll(RegExp(r"/+$"), "")}/api/v1/auth/logout'),
        headers: {'Authorization': 'Bearer $token'}).timeout(const Duration(seconds: 10));
    } catch (_) {}
  }

  Future<void> _start() async {
    if (processing || recording) return;
    try {
      if (!await _recorder.hasPermission()) {
        throw StateError('Microphone permission is required.');
      }
      final dir = await getTemporaryDirectory();
      final path = '${dir.path}/arevik-recording.wav';
      await _recorder.start(const RecordConfig(encoder: AudioEncoder.wav,
        sampleRate: 16000, numChannels: 1), path: path);
      if (!mounted) return;
      setState(() { recording = true; stage = 'Recording...'; error = null; });
    } catch (e) {
      if (mounted) setState(() { error = 'Unable to record: $e'; stage = 'Ready'; });
    }
  }

  Future<void> _stopAndTranslate() async {
    if (!recording) return;
    setState(() { recording = false; processing = true; stage = 'Recognizing & translating...'; error = null; });
    try {
      recordedPath = await _recorder.stop();
      final path = recordedPath;
      if (path == null || !File(path).existsSync()) throw StateError('Recording was not saved');
      final url = Uri.parse('${_server.text.trim().replaceAll(RegExp(r"/+$"), "")}/api/v1/translate/file');
      if (url.scheme != 'https' && !(url.host == '10.0.2.2' || url.host == '127.0.0.1' || url.host == 'localhost')) {
        throw StateError('Use HTTPS for remote servers.');
      }
      final request = http.MultipartRequest('POST', url);
      if (_accessToken.text.trim().isNotEmpty) {
        request.headers['Authorization'] = 'Bearer ${_accessToken.text.trim()}';
      }
      request.fields['source_language'] = source
        ..fields['target_language'] = target
        ..files.add(await http.MultipartFile.fromPath('file', path, filename: 'recording.wav'));
      final streamed = await request.send().timeout(const Duration(seconds: 90));
      final response = await http.Response.fromStream(streamed);
      if (response.statusCode != 200) throw StateError('Server ${response.statusCode}: ${response.body}');
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final bytes = base64Decode((payload['audio'] as Map<String,dynamic>)['data'] as String);
      final dir = await getTemporaryDirectory();
      spokenFile = '${dir.path}/arevik-translated.wav';
      await File(spokenFile!).writeAsBytes(bytes, flush: true);
      if (!mounted) return;
      setState(() {
        original = payload['source_text'] as String? ?? '';
        translation = payload['translated_text'] as String? ?? '';
        stage = 'Translated';
      });
      await _player.play(DeviceFileSource(spokenFile!));
    } catch (e) {
      if (mounted) setState(() { error = e.toString(); stage = 'Retry'; });
    } finally {
      final path = recordedPath;
      if (path != null) { try { await File(path).delete(); } catch (_) {} }
      if (mounted) setState(() => processing = false);
    }
  }

  void _swap() {
    if (recording || processing) return;
    setState(() { final old = source; source = target; target = old; });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Arevik AI'), centerTitle: false,
      backgroundColor: Colors.transparent),
    body: SafeArea(child: ListView(padding: const EdgeInsets.all(20), children: [
      if (!_authenticated) ...[
        const Text('Sign in', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),
        TextField(controller: _email, decoration: const InputDecoration(labelText: 'Email', border: OutlineInputBorder())),
        const SizedBox(height: 10),
        TextField(controller: _password, obscureText: true,
          decoration: const InputDecoration(labelText: 'Password', border: OutlineInputBorder())),
        const SizedBox(height: 10),
        TextField(controller: _server,
          decoration: const InputDecoration(labelText: 'HTTPS API URL', border: OutlineInputBorder())),
        const SizedBox(height: 12),
        FilledButton(onPressed: processing ? null : () => _login(), child: const Text('Sign in')),
        OutlinedButton(onPressed: processing ? null : () => _login(register: true), child: const Text('Create account')),
        if (error != null) Text(error!, style: const TextStyle(color: Colors.red)),
      ] else ...[
        Align(alignment: Alignment.centerRight,
          child: TextButton(onPressed: _logout, child: const Text('Sign out'))),
      const Text('Understand each other.', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
      const SizedBox(height: 5),
      const Text('Early MVP • Push-to-talk translation', style: TextStyle(color: Colors.black54)),
      const SizedBox(height: 25),
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(children: [
        const Align(alignment: Alignment.centerLeft,
          child: Text('Language direction', style: TextStyle(fontWeight: FontWeight.bold))),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(child: _languagePicker(source, (v) => setState(() { source=v; if (source == target) target = v == 'en' ? 'hy':'en'; }))),
          IconButton(onPressed: recording || processing ? null : _swap, icon: const Icon(Icons.swap_horiz)),
          Expanded(child: _languagePicker(target, (v) => setState(() { target=v; if (source == target) source = v == 'en' ? 'hy':'en'; }))),
        ]),
      ]))),
      const SizedBox(height: 16),
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
        crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Connection', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          TextField(controller: _server, enabled: !recording && !processing,
            decoration: const InputDecoration(labelText: 'API base URL',
              hintText: 'https://your-server.example', border: OutlineInputBorder()),
            keyboardType: TextInputType.url),
          const SizedBox(height: 8),
          const Text('Authenticated session active'),
          const SizedBox(height: 8),
          const Text('For Android emulator use 10.0.2.2 with an SSH tunnel. '
            'Real phones require an authenticated HTTPS endpoint.',
            style: TextStyle(fontSize: 12, color: Colors.black54)),
        ]))),
      const SizedBox(height: 22),
      Center(child: Text(stage, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600))),
      const SizedBox(height: 14),
      Center(child: SizedBox(width: 112, height: 112, child: FilledButton(
        onPressed: processing ? null : recording ? _stopAndTranslate : _start,
        style: FilledButton.styleFrom(shape: const CircleBorder(),
          backgroundColor: recording ? Colors.redAccent : null),
        child: Icon(recording ? Icons.stop : Icons.mic, size: 46),
      ))),
      const SizedBox(height: 10),
      Center(child: Text(recording ? 'Tap to stop & translate' : 'Tap to speak')),
      if (processing) const Padding(padding: EdgeInsets.only(top: 12),
        child: LinearProgressIndicator()),
      if (error != null) Padding(padding: const EdgeInsets.only(top: 16),
        child: SelectableText(error!, style: const TextStyle(color: Colors.red))),
      const SizedBox(height: 24),
      _resultCard('You said', original.isEmpty ? 'Your speech transcript appears here' : original),
      const SizedBox(height: 12),
      _resultCard('Translation', translation.isEmpty ? 'Translation appears here' : translation),
      const SizedBox(height: 16),
      OutlinedButton.icon(
        onPressed: spokenFile == null ? null : () => _player.play(DeviceFileSource(spokenFile!)),
        icon: const Icon(Icons.volume_up), label: const Text('Replay translation')),
      const SizedBox(height: 15),
      const Text('Persian, paired sessions, and live streaming are being integrated. '
        'This prototype currently uses the existing English–Armenian file API.',
        style: TextStyle(color: Colors.black54, fontSize: 12)),
      ],
    ])),
  );

  Widget _languagePicker(String value, ValueChanged<String> onChanged) =>
    DropdownButtonFormField<String>(value: value,
      decoration: const InputDecoration(border: OutlineInputBorder()),
      items: const [
        DropdownMenuItem(value: 'en', child: Text('English')),
        DropdownMenuItem(value: 'hy', child: Text('Armenian')),
      ], onChanged: recording || processing ? null : onChanged);

  Widget _resultCard(String title, String body) =>
    Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(fontSize: 13, color: Colors.black54)),
        const SizedBox(height: 8),
        SelectableText(body, style: const TextStyle(fontSize: 18)),
      ])));
}
