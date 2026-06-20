import 'dart:async';

import 'package:package_info_plus/package_info_plus.dart';

Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  PackageInfo.setMockInitialValues(
    appName: 'GoTrendLabs',
    packageName: 'br.com.gotrendlabs.app',
    version: '1.0.8',
    buildNumber: '9',
    buildSignature: '',
  );
  await testMain();
}
