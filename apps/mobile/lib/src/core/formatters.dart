String formatGtl(num value) => '${value.round()} GT₵';

String formatProbability(num value) => '${value.round()}%';

String compactText(String value, {int max = 120}) {
  final normalized = value.trim().replaceAll(RegExp(r'\s+'), ' ');
  if (normalized.length <= max) {
    return normalized;
  }
  return '${normalized.substring(0, max - 1)}…';
}

String safeString(Object? value, [String fallback = '']) {
  if (value == null) {
    return fallback;
  }
  return value.toString();
}

int safeInt(Object? value, [int fallback = 0]) {
  if (value is int) {
    return value;
  }
  if (value is num) {
    return value.round();
  }
  return int.tryParse(value?.toString() ?? '') ?? fallback;
}

double safeDouble(Object? value, [double fallback = 0]) {
  if (value is double) {
    return value;
  }
  if (value is num) {
    return value.toDouble();
  }
  return double.tryParse(value?.toString() ?? '') ?? fallback;
}

bool safeBool(Object? value, [bool fallback = false]) {
  if (value is bool) {
    return value;
  }
  return fallback;
}
