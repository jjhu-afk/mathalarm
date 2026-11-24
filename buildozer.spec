[app]
title = MathAlarm
package.name = mathalarm
package.domain = ru.penzgtu
source.dir = .
source.include_exts = py,kv,png,jpg
source.exclude_dirs = tests,docs
version = 0.2.0
requirements = python3,kivy==2.3.2,sqlite3,pyjnius
orientation = portrait
fullscreen = 0
android.minapi = 24
android.api = 36
android.ndk = 29
android.archs = arm64-v8a
android.add_src = android_src
android.extra_manifest_application_arguments = android_src/application.xml
android.permissions = android.permission.USE_EXACT_ALARM, (name=android.permission.SCHEDULE_EXACT_ALARM;maxSdkVersion=32), android.permission.RECEIVE_BOOT_COMPLETED, android.permission.POST_NOTIFICATIONS, android.permission.USE_FULL_SCREEN_INTENT, android.permission.FOREGROUND_SERVICE, android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK
android.accept_sdk_license = True
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
