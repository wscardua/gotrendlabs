class AppEnvironment {
  static const apiBaseUrl = String.fromEnvironment(
    'GTL_API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8001',
  );

  static const publicWebBaseUrl = String.fromEnvironment(
    'GTL_PUBLIC_WEB_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const pushFakeToken = String.fromEnvironment(
    'GTL_PUSH_FAKE_TOKEN',
    defaultValue: '',
  );

  static const pushFakePlatform = String.fromEnvironment(
    'GTL_PUSH_FAKE_PLATFORM',
    defaultValue: 'android',
  );

  static const pushFakeDeviceLabel = String.fromEnvironment(
    'GTL_PUSH_FAKE_DEVICE_LABEL',
    defaultValue: 'Emulador local',
  );
}
