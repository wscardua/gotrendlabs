import 'package:flutter/material.dart';

class GtlColors {
  static const background = Color(0xFF050608);
  static const backgroundAlt = Color(0xFF080D12);
  static const surface = Color(0xFF11151B);
  static const surfaceElevated = Color(0xFF191F27);
  static const surfaceGlass = Color(0xD9141921);
  static const surfaceInk = Color(0xFF0B1016);
  static const border = Color(0x2EFFFFFF);
  static const borderStrong = Color(0x52FFFFFF);
  static const textPrimary = Color(0xFFF3F6F8);
  static const textSecondary = Color(0xFFB7C0CA);
  static const muted = Color(0xFF78828F);
  static const accentBlue = Color(0xFF35A7FF);
  static const accentCyan = Color(0xFF4CE6C8);
  static const accentGreen = Color(0xFF55D47A);
  static const accentRed = Color(0xFFFF6B6B);
  static const accentYellow = Color(0xFFFFC857);
  static const accentViolet = Color(0xFFA98BFF);
}

class GtlRadii {
  static const small = 8.0;
  static const medium = 12.0;
  static const large = 18.0;
  static const pill = 999.0;
}

class GtlShadows {
  static List<BoxShadow> glow(Color color, {double opacity = 0.22}) => [
    BoxShadow(
      color: color.withValues(alpha: opacity),
      blurRadius: 28,
      spreadRadius: -12,
      offset: const Offset(0, 14),
    ),
  ];
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
      surfaceContainerHighest: GtlColors.surfaceElevated,
    ),
    scaffoldBackgroundColor: GtlColors.background,
    fontFamily: 'Avenir Next',
    textTheme: const TextTheme(
      displaySmall: TextStyle(
        color: GtlColors.textPrimary,
        fontWeight: FontWeight.w800,
        letterSpacing: 0,
      ),
      headlineMedium: TextStyle(
        color: GtlColors.textPrimary,
        fontWeight: FontWeight.w900,
        letterSpacing: 0,
        height: 1.02,
      ),
      headlineSmall: TextStyle(
        color: GtlColors.textPrimary,
        fontWeight: FontWeight.w800,
        letterSpacing: 0,
        height: 1.06,
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
      bodySmall: TextStyle(color: GtlColors.muted, letterSpacing: 0),
      labelLarge: TextStyle(
        color: GtlColors.textPrimary,
        fontWeight: FontWeight.w800,
        letterSpacing: 0,
      ),
      labelMedium: TextStyle(
        color: GtlColors.textSecondary,
        fontWeight: FontWeight.w700,
        letterSpacing: 0,
      ),
      labelSmall: TextStyle(
        color: GtlColors.muted,
        fontWeight: FontWeight.w800,
        letterSpacing: 0,
      ),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: GtlColors.background,
      foregroundColor: GtlColors.textPrimary,
      elevation: 0,
      centerTitle: false,
      surfaceTintColor: Colors.transparent,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: GtlColors.surfaceInk,
      elevation: 0,
      indicatorColor: GtlColors.accentBlue.withValues(alpha: 0.20),
      surfaceTintColor: Colors.transparent,
      height: 68,
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
    chipTheme: ChipThemeData(
      backgroundColor: GtlColors.surfaceElevated,
      selectedColor: GtlColors.accentBlue.withValues(alpha: 0.20),
      disabledColor: GtlColors.surface,
      side: const BorderSide(color: GtlColors.border),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(GtlRadii.pill),
      ),
      labelStyle: const TextStyle(
        color: GtlColors.textSecondary,
        fontWeight: FontWeight.w800,
        letterSpacing: 0,
      ),
      secondaryLabelStyle: const TextStyle(
        color: GtlColors.textPrimary,
        fontWeight: FontWeight.w800,
        letterSpacing: 0,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: GtlColors.surfaceElevated,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(GtlRadii.medium),
        borderSide: const BorderSide(color: GtlColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(GtlRadii.medium),
        borderSide: const BorderSide(color: GtlColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(GtlRadii.medium),
        borderSide: const BorderSide(color: GtlColors.accentBlue),
      ),
      labelStyle: const TextStyle(color: GtlColors.textSecondary),
      prefixIconColor: GtlColors.muted,
    ),
    cardTheme: CardThemeData(
      color: GtlColors.surface,
      elevation: 0,
      margin: EdgeInsets.zero,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(GtlRadii.medium),
        side: const BorderSide(color: GtlColors.border),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: GtlColors.textPrimary,
        foregroundColor: GtlColors.background,
        minimumSize: const Size.fromHeight(48),
        textStyle: const TextStyle(
          fontWeight: FontWeight.w900,
          letterSpacing: 0,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GtlRadii.medium),
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: GtlColors.textPrimary,
        minimumSize: const Size.fromHeight(46),
        side: const BorderSide(color: GtlColors.borderStrong),
        textStyle: const TextStyle(
          fontWeight: FontWeight.w800,
          letterSpacing: 0,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GtlRadii.medium),
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: GtlColors.accentBlue,
        textStyle: const TextStyle(
          fontWeight: FontWeight.w800,
          letterSpacing: 0,
        ),
      ),
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: ButtonStyle(
        backgroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? GtlColors.accentBlue.withValues(alpha: 0.20)
              : GtlColors.surfaceInk,
        ),
        foregroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? GtlColors.textPrimary
              : GtlColors.textSecondary,
        ),
        side: WidgetStateProperty.all(
          const BorderSide(color: GtlColors.border),
        ),
        textStyle: WidgetStateProperty.all(
          const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 0),
        ),
      ),
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: GtlColors.surfaceElevated,
      surfaceTintColor: Colors.transparent,
      modalBackgroundColor: GtlColors.surfaceElevated,
    ),
  );
}
