import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:arevik_mobile/main.dart';

void main() {
  testWidgets('MVP renders sign-in before interpreter access', (tester) async {
    await tester.pumpWidget(const ArevikApp());
    expect(find.text('Arevik AI'), findsOneWidget);
    expect(find.text('Sign in'), findsWidgets);
    expect(find.text('Create account'), findsOneWidget);
  });
}
