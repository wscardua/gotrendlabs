import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

abstract class BiometricPreferenceStore {
  Future<bool> readEnabled();
  Future<void> writeEnabled(bool enabled);
}

class SecureBiometricPreferenceStore implements BiometricPreferenceStore {
  SecureBiometricPreferenceStore() : _storage = const FlutterSecureStorage();

  static const _key = 'gotrendlabs.biometric.enabled';
  final FlutterSecureStorage _storage;

  @override
  Future<bool> readEnabled() async {
    return await _storage.read(key: _key) == '1';
  }

  @override
  Future<void> writeEnabled(bool enabled) {
    if (!enabled) {
      return _storage.delete(key: _key);
    }
    return _storage.write(key: _key, value: '1');
  }
}

class MemoryBiometricPreferenceStore implements BiometricPreferenceStore {
  MemoryBiometricPreferenceStore({this.enabled = false});

  bool enabled;

  @override
  Future<bool> readEnabled() async => enabled;

  @override
  Future<void> writeEnabled(bool enabled) async {
    this.enabled = enabled;
  }
}

abstract class BiometricAuthenticator {
  Future<bool> isSupported();
  Future<bool> authenticate({required String reason});
}

class LocalBiometricAuthenticator implements BiometricAuthenticator {
  LocalBiometricAuthenticator({LocalAuthentication? auth})
    : _auth = auth ?? LocalAuthentication();

  final LocalAuthentication _auth;

  @override
  Future<bool> isSupported() async {
    try {
      return await _auth.isDeviceSupported() || await _hasEnrolledBiometrics();
    } catch (_) {
      return false;
    }
  }

  @override
  Future<bool> authenticate({required String reason}) async {
    try {
      return await _auth.authenticate(
        localizedReason: reason,
        biometricOnly: false,
        persistAcrossBackgrounding: true,
      );
    } on LocalAuthException {
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<bool> _hasEnrolledBiometrics() async {
    final biometrics = await _auth.getAvailableBiometrics();
    return biometrics.isNotEmpty;
  }
}
