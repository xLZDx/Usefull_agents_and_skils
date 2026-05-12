---
name: fitness-app-helper
description: Context loader template for a Flutter + Firebase fitness app project. Customize paths under `<project-root>` for your own setup. Use when working on the Flutter mobile app, Firebase backend, Cloud Functions, debug daemon, Stripe test integration, or any source under the project directory.
---

# Fitness App — Skill Context (template)

This skill loads architectural truth for a fitness/health Flutter app so you don't have to grep for it.

> Replace `<project-root>` and SDK paths with your own absolute paths before use.

## Stack
- **Frontend:** Flutter 3.x + Dart + Riverpod + go_router (Material 3)
- **Backend:** Firebase Auth, Firestore, Storage, Cloud Functions (TypeScript)
- **Payments:** Stripe (test mode); App Store IAP planned for iOS
- **Target:** Android-first, iOS on roadmap. Design every package + abstraction to accommodate iOS from day one.

## Layout
- Project root: `<project-root>`
- App: `mobile/lib/main.dart`
- Cloud Functions: `functions/`
- Routes: `mobile/lib/core/router/`
- Features: `mobile/lib/features/{splash,auth,home,scanner,workouts,progress,profile}/`
- Theme: `mobile/lib/core/theme/`
- Shared widgets: `mobile/lib/shared/widgets/`

## Cross-platform principle
- No Android-only APIs in shared code.
- Abstraction layer for Health Connect ↔ HealthKit (`HealthService` interface, platform-specific impls + Mock).
- Wear OS first, Apple Watch later — phone-side wear comms is a generic interface.
- Cupertino-style fallbacks selectively on iOS (date pickers, switches, action sheets).
- App Store IAP planned alongside Stripe: `SubscriptionAction` abstract surface; `StoreKitCheckoutService` (iOS) alongside `CloudFunctionsStripeService` (Android + web).

## Debug daemon (READ FIRST for bug reports)
- Runbook: `core/DEBUGGING.md`
- Launcher: `scripts/dev/debug_daemon.ps1`
- Per-session captures: `logs/sessions/<latest>/` — flutter logs, errors, touches, screencaps, Cloud Functions logs.
- For any bug report: **read the latest session log before guessing.**

## Stripe test mode
- Price IDs documented in: `core/PHASE_4B_STRIPE_SETUP.md`
- Secrets via env vars (`.env`, never committed; `.env.example` for templates).
- Subscriptions can be framed as donations under a 501(c)(3) plan if applicable.

## Plan & reference docs
- `core/ROADMAP_<version>.md` — sequenced P0/P1/P2 + Tier-X game-changer features.
- `core/COMPETITIVE_ASSESSMENT.md` — competitor analysis & feature gaps.
- `core/NONPROFIT_PLAN.md` — 501(c)(3) / fiscal-sponsor strategy (optional).
- `core/IMPLEMENTATION_PLAN.md` — live phase/sequence roadmap.

## Toolchain (off-system-drive policy)
- Flutter SDK: `<sdk-root>/flutter`
- Android SDK: `<sdk-root>/android-sdk`
- AVD: configured under `<sdk-root>/android-sdk/avd`
- JDK: a system install acceptable (documented bridge); no project data lands there.
- Env vars pinned off system drive: `PUB_CACHE`, `GRADLE_USER_HOME`, `TEMP`, `TMP`, `ANDROID_AVD_HOME`, `ANDROID_SDK_ROOT`, `FLUTTER_ROOT`.

## Tests
- `mobile/test/` — Flutter widget + unit tests.
- `mobile/integration_test/` — integration tests.
- `flutter analyze` + `flutter test` after every change. 0 failures required.
- For UI changes: `flutter build apk --debug` + install on emulator and **visually verify**.

## Inherits global rules
This project inherits rules from `<workspace-root>/CLAUDE.md` (approval gate, no-guessing, regression tests, disk policy, git lifecycle including todo-in-commits, functional tests prove behavior).
