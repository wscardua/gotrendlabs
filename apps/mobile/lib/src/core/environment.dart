class AppEnvironment {
  static const apiBaseUrl = String.fromEnvironment(
    'GTL_API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8001',
  );

  static const publicWebBaseUrl = String.fromEnvironment(
    'GTL_PUBLIC_WEB_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}
