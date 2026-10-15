import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:arevik_mobile/main.dart';

void main() {
  testWidgets('MVP renders recording control and language choice', (tester) async {
    await tester.pumpWidget(const ArevikApp());
    expect(find.text('Arevik AI'), findsOneWidget);
    expect(find.text('Language direction'), findsOneWidget);
    expect(find.byIcon(Icons.mic), findsOneWidget);
    expect(find.text('Translation'), findsOneWidget);
  });
}
