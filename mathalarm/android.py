"""Platform boundary for Android AlarmManager and the ringing service."""

from kivy.utils import platform


class AndroidAlarms:
    def __init__(self):
        self.available = platform == "android"
        if self.available:
            from jnius import autoclass

            self.activity = autoclass("org.kivy.android.PythonActivity").mActivity
            self.bridge = autoclass("ru.penzgtu.mathalarm.AlarmBridge")
            self.context = self.activity.getApplicationContext()

    def can_schedule(self):
        return self.available and bool(self.bridge.canSchedule(self.context))

    def schedule(self, alarm):
        if not self.available:
            return False
        return bool(self.bridge.schedule(
            self.context, alarm.id, alarm.hour, alarm.minute, alarm.days_mask
        ))

    def cancel(self, alarm_id):
        if self.available:
            self.bridge.cancel(self.context, alarm_id)

    def ringing_id(self):
        return int(self.bridge.getRingingId(self.context)) if self.available else -1

    def stop(self, alarm_id):
        if self.available:
            self.bridge.stopRinging(self.context, alarm_id)

    def current_intent_id(self):
        if not self.available:
            return -1
        intent = self.activity.getIntent()
        if intent is None:
            return -1
        alarm_id = int(intent.getIntExtra("mathalarm_alarm_id", -1))
        intent.removeExtra("mathalarm_alarm_id")
        return alarm_id

    def request_notifications(self):
        if self.available:
            from android.permissions import request_permissions

            request_permissions(["android.permission.POST_NOTIFICATIONS"])

    def open_alarm_settings(self):
        if not self.available:
            return
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        Settings = autoclass("android.provider.Settings")
        Uri = autoclass("android.net.Uri")
        intent = Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM)
        intent.setData(Uri.parse("package:" + self.context.getPackageName()))
        self.activity.startActivity(intent)

    def system_insets(self):
        if not self.available:
            return (0, 0)
        from jnius import autoclass

        insets = self.activity.getWindow().getDecorView().getRootWindowInsets()
        if insets is None:
            return (0, 0)
        sdk = autoclass("android.os.Build$VERSION").SDK_INT
        if sdk >= 30:
            type_class = autoclass("android.view.WindowInsets$Type")
            bars = insets.getInsets(type_class.systemBars())
            return (int(bars.top), int(bars.bottom))
        return (int(insets.getSystemWindowInsetTop()),
                int(insets.getSystemWindowInsetBottom()))
