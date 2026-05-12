---
name: fitness-app-helper
description: Context loader for the Fitness App project at D:\test 2\Fitness App. Use when working on the Flutter mobile app, Firebase backend, Cloud Functions, debug daemon, Stripe test integration, or any source under that directory. Loads architecture, debug daemon location, Stripe test config, and roadmap pointers.
---

# Fitness App — Skill Context

This skill loads the project's architectural truth so you don't have to grep for it.

## Stack
- **Frontend:** Flutter 3.x + Dart + Riverpod + go_router (Material 3)
- **Backend:** Firebase Auth, Firestore, Storage, Cloud Functions (TypeScript)
- **Payments:** Stripe (test mode); App Store IAP planned for iOS
- **Target:** Android-first, iOS on roadmap. Design every package + abstraction to accommodate iOS from day one.

## Layout
- Project root: `D:\test 2\Fitness App`
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
- Price IDs: `core/PHASE_4B_STRIPE_SETUP.md`
- Secrets via env vars (`.env`, never committed; `.env.example` for templates)
- Subscriptions framed as donations under the 501(c)(3) plan.

## Plan & reference docs
- `core/ROADMAP_2026_V2.md` — sequenced P0/P1/P2 + 7 Tier-X game-changer features (Injury Recovery Coach, Visual recognition, Buddy Matching, Auto-deload, Coach Marketplace, Voice-only, Equipment Reporting).
- `core/COMPETITIVE_ASSESSMENT.md` — vs 15 competitors as of 2026-05-09; QR-scan + injury-filter are moats; Wear OS / videos / annual pricing are P0 gaps.
- `core/NONPROFIT_PLAN.md` — 501(c)(3) / fiscal-sponsor strategy; subscriptions=donations; celebrity content=in-kind donations; year-1 cash spend ~$5k self-sustaining at 50 paying donors.
- `core/IMPLEMENTATION_PLAN.md` — live phase/sequence roadmap.
- `FITNESS_APP_TASK_LIST.md` (in trading-assistance dir) — master 75-feature list.

## Toolchain (D: drive only — see global disk policy)
- Flutter SDK: `D:\flutter`
- Android SDK: `D:\android-sdk`
- AVD: `Pixel_API_34` (under `D:\android-sdk\avd`)
- JDK: `C:\Program Files\Microsoft\jdk-17.0.18.8-hotspot` — system install, documented C: bridge; no project data lands there.
- Env vars pinned to D:: `PUB_CACHE`, `GRADLE_USER_HOME`, `TEMP`, `TMP`, `ANDROID_AVD_HOME`, `ANDROID_SDK_ROOT`, `FLUTTER_ROOT`.

## Tests
- `mobile/test/` — Flutter widget + unit tests (315+ tests passing as of 2026-05-10).
- `mobile/integration_test/` — integration tests.
- `flutter analyze` + `flutter test` after every change. 0 failures required.
- For UI changes: `flutter build apk --debug` + install on emulator and **visually verify**.

## Inherits global rules
This project inherits all rules from `D:\test 2\CLAUDE.md` (approval gate, no-guessing, regression tests, D:-drive-only, git lifecycle including todo-in-commits, functional tests prove behavior).
