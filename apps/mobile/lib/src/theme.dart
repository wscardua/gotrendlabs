import 'package:flutter/material.dart';

class GtlColors {
  static const background = Color(0xFF050608);
  static const surface = Color(0xFF11151B);
  static const surfaceElevated = Color(0xFF191F27);
  static const border = Color(0x2EFFFFFF);
  static const textPrimary = Color(0xFFF3F6F8);
  static const textSecondary = Color(0xFFB7C0CA);
  static const muted = Color(0xFF78828F);
  static const accentBlue = Color(0xFF35A7FF);
  static const accentGreen = Color(0xFF55D47A);
  static const accentRed = Color(0xFFFF6B6B);
  static const accentYellow = Color(0xFFFFC857);
  static const accentViolet = Color(0xFFA98BFF);
}

ThemeData buildGoTrendLabsTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: GtlColors.accentBlue,
    brightness: Brightness.dark,
    surface: GtlColors.surface,
  );

  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: scheme.copyWith(
      primary: GtlColors.accentBlue,
      secondary: GtlColors.accentGreen,
      error: GtlColors.accentRed,
      surface: GtlColors.surface,
    ),
    scaffoldBackgroundColor: GtlColors.background,
    fontFamily: 'Avenir Next',
    textTheme: const TextTheme(
      displaySmall: TextStyle(
        color: GtlColors.textPrimary,
        fontWeight: FontWeight.w800,
        letterSpacing: 0,
      ),
      headlineSmall: TextStyle(
        color: GtlColors.textPrimary,
        fontWeight: FontWeight.w800,
        letterSpacing: 0,
      ),
      titleLarge: TextStyle(
        color: GtlColors.textPrimary,
        fontWeight: FontWeight.w800,
        letterSpacing: 0,
      ),
      titleMedium: TextStyle(
        color: GtlColors.textPrimary,
        fontWeight: FontWeight.w700,
        letterSpacing: 0,
      ),
      bodyLarge: TextStyle(color: GtlColors.textPrimary, letterSpacing: 0),
      bodyMedium: TextStyle(color: GtlColors.textSecondary, letterSpacing: 0),
      labelMedium: TextStyle(
        color: GtlColors.textSecondary,
        fontWeight: FontWeight.w700,
        letterSpacing: 0,
      ),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: GtlColors.background,
      foregroundColor: GtlColors.textPrimary,
      elevation: 0,
      centerTitle: false,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: GtlColors.surface,
      indicatorColor: GtlColors.accentBlue.withValues(alpha: 0.16),
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          color: states.contains(WidgetState.selected)
              ? GtlColors.textPrimary
              : GtlColors.muted,
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 0,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected)
              ? GtlColors.accentBlue
              : GtlColors.muted,
          size: 22,
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: GtlColors.surfaceElevated,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: GtlColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: GtlColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: GtlColors.accentBlue),
      ),
    ),
    cardTheme: CardThemeData(
      color: GtlColors.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: GtlColors.border),
      ),
    ),
  );
}
