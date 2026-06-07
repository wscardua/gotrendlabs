import 'package:flutter/material.dart';

import '../theme.dart';

class GtlScreen extends StatelessWidget {
  const GtlScreen({super.key, required this.child, this.padding});

  final Widget child;
  final EdgeInsetsGeometry? padding;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            GtlColors.backgroundAlt,
            GtlColors.background,
            Color(0xFF07090C),
          ],
        ),
      ),
      child: Padding(padding: padding ?? EdgeInsets.zero, child: child),
    );
  }
}

class GtlSurface extends StatelessWidget {
  const GtlSurface({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.color,
    this.borderColor,
    this.glowColor,
    this.onTap,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color? color;
  final Color? borderColor;
  final Color? glowColor;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final decoration = BoxDecoration(
      color: color ?? GtlColors.surface,
      borderRadius: BorderRadius.circular(GtlRadii.medium),
      border: Border.all(color: borderColor ?? GtlColors.border),
      boxShadow: glowColor == null ? null : GtlShadows.glow(glowColor!),
    );
    final content = Container(
      decoration: decoration,
      child: Padding(padding: padding, child: child),
    );
    if (onTap == null) {
      return content;
    }
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(GtlRadii.medium),
        onTap: onTap,
        child: content,
      ),
    );
  }
}

class GtlEditorialHeader extends StatelessWidget {
  const GtlEditorialHeader({
    super.key,
    required this.title,
    this.kicker,
    this.body,
    this.trailing,
    this.icon,
  });

  final String title;
  final String? kicker;
  final String? body;
  final Widget? trailing;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (icon != null) ...[
          DecoratedBox(
            decoration: BoxDecoration(
              color: GtlColors.accentBlue.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(GtlRadii.medium),
              border: Border.all(color: GtlColors.border),
            ),
            child: Padding(
              padding: const EdgeInsets.all(10),
              child: Icon(icon, color: GtlColors.accentBlue),
            ),
          ),
          const SizedBox(width: 12),
        ],
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (kicker?.trim().isNotEmpty == true) ...[
                Text(
                  kicker!.toUpperCase(),
                  style: Theme.of(
                    context,
                  ).textTheme.labelSmall?.copyWith(color: GtlColors.accentCyan),
                ),
                const SizedBox(height: 5),
              ],
              Text(title, style: Theme.of(context).textTheme.headlineSmall),
              if (body?.trim().isNotEmpty == true) ...[
                const SizedBox(height: 8),
                Text(body!, style: Theme.of(context).textTheme.bodyMedium),
              ],
            ],
          ),
        ),
        if (trailing != null) ...[const SizedBox(width: 12), trailing!],
      ],
    );
  }
}

class GtlBrandMark extends StatelessWidget {
  const GtlBrandMark({super.key, this.size = 48});

  final double size;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: GtlColors.surfaceElevated,
        borderRadius: BorderRadius.circular(size * 0.26),
        border: Border.all(color: GtlColors.borderStrong),
        boxShadow: GtlShadows.glow(GtlColors.accentBlue, opacity: 0.16),
      ),
      child: SizedBox.square(
        dimension: size,
        child: Stack(
          alignment: Alignment.center,
          children: [
            Positioned(
              left: size * 0.18,
              top: size * 0.18,
              child: Icon(
                Icons.auto_awesome,
                size: size * 0.26,
                color: GtlColors.accentBlue,
              ),
            ),
            Icon(
              Icons.show_chart,
              size: size * 0.54,
              color: GtlColors.textPrimary,
            ),
          ],
        ),
      ),
    );
  }
}

class GtlSectionTitle extends StatelessWidget {
  const GtlSectionTitle({
    super.key,
    required this.title,
    this.subtitle,
    this.trailing,
  });

  final String title;
  final String? subtitle;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: Theme.of(context).textTheme.titleLarge),
              if (subtitle?.trim().isNotEmpty == true) ...[
                const SizedBox(height: 3),
                Text(subtitle!, style: Theme.of(context).textTheme.bodySmall),
              ],
            ],
          ),
        ),
        ?trailing,
      ],
    );
  }
}

class GtlPill extends StatelessWidget {
  const GtlPill({
    super.key,
    required this.label,
    this.icon,
    this.color = GtlColors.accentBlue,
    this.filled = false,
  });

  final String label;
  final IconData? icon;
  final Color color;
  final bool filled;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: filled
            ? color.withValues(alpha: 0.20)
            : Colors.black.withValues(alpha: 0.28),
        borderRadius: BorderRadius.circular(GtlRadii.pill),
        border: Border.all(color: color.withValues(alpha: 0.44)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(icon, size: 14, color: color),
              const SizedBox(width: 6),
            ],
            Text(
              label,
              style: Theme.of(
                context,
              ).textTheme.labelMedium?.copyWith(color: GtlColors.textPrimary),
            ),
          ],
        ),
      ),
    );
  }
}

class GtlMetricTile extends StatelessWidget {
  const GtlMetricTile({
    super.key,
    required this.label,
    required this.value,
    this.icon,
    this.color = GtlColors.accentBlue,
  });

  final String label;
  final String value;
  final IconData? icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: GtlColors.surfaceInk,
        borderRadius: BorderRadius.circular(GtlRadii.medium),
        border: Border.all(color: GtlColors.border),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Row(
              children: [
                if (icon != null) ...[
                  Icon(icon, size: 15, color: color),
                  const SizedBox(width: 6),
                ],
                Expanded(
                  child: Text(
                    label.toUpperCase(),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelSmall,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 7),
            FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: Text(value, style: Theme.of(context).textTheme.titleLarge),
            ),
          ],
        ),
      ),
    );
  }
}

class GtlStatePanel extends StatelessWidget {
  const GtlStatePanel({
    super.key,
    required this.icon,
    required this.title,
    required this.body,
    this.action,
    this.color = GtlColors.accentBlue,
  });

  final IconData icon;
  final String title;
  final String body;
  final Widget? action;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: GtlSurface(
          glowColor: color,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(GtlRadii.pill),
                  border: Border.all(color: color.withValues(alpha: 0.42)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Icon(icon, color: color, size: 30),
                ),
              ),
              const SizedBox(height: 14),
              Text(
                title,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Text(
                body,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              if (action != null) ...[const SizedBox(height: 16), action!],
            ],
          ),
        ),
      ),
    );
  }
}

class GtlSkeletonBlock extends StatelessWidget {
  const GtlSkeletonBlock({super.key, required this.height, this.width});

  final double height;
  final double? width;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: GtlColors.surfaceElevated.withValues(alpha: 0.78),
        borderRadius: BorderRadius.circular(GtlRadii.medium),
        border: Border.all(color: GtlColors.border),
      ),
    );
  }
}
