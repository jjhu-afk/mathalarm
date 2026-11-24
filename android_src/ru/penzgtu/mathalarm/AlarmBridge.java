package ru.penzgtu.mathalarm;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import java.util.Calendar;
import java.util.HashSet;
import java.util.Set;

/** Small Android bridge; SQLite remains the source of truth for alarm settings. */
public final class AlarmBridge {
    static final String PREFS = "mathalarm_schedules";
    static final String IDS = "ids";
    static final String RINGING = "ringing_id";
    public static final String EXTRA_ID = "mathalarm_alarm_id";

    private AlarmBridge() { }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static boolean canSchedule(Context context) {
        if (Build.VERSION.SDK_INT < 31) return true;
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        return manager != null && manager.canScheduleExactAlarms();
    }

    private static PendingIntent fireIntent(Context context, int id) {
        Intent intent = new Intent(context, AlarmReceiver.class);
        intent.putExtra(EXTRA_ID, id);
        return PendingIntent.getBroadcast(context, id, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    static long nextTime(int hour, int minute, int daysMask) {
        Calendar now = Calendar.getInstance();
        for (int offset = 0; offset < 8; offset++) {
            Calendar candidate = (Calendar) now.clone();
            candidate.add(Calendar.DAY_OF_YEAR, offset);
            int weekday = (candidate.get(Calendar.DAY_OF_WEEK) + 5) % 7; // Monday = 0
            if ((daysMask & (1 << weekday)) == 0) continue;
            candidate.set(Calendar.HOUR_OF_DAY, hour);
            candidate.set(Calendar.MINUTE, minute);
            candidate.set(Calendar.SECOND, 0);
            candidate.set(Calendar.MILLISECOND, 0);
            if (candidate.after(now)) return candidate.getTimeInMillis();
        }
        throw new IllegalArgumentException("No future alarm time");
    }

    public static boolean schedule(Context context, int id, int hour, int minute, int daysMask) {
        if (id < 1 || hour < 0 || hour > 23 || minute < 0 || minute > 59
                || daysMask < 1 || daysMask > 127 || !canSchedule(context)) return false;
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (manager == null) return false;
        Intent open = new Intent(context, org.kivy.android.PythonActivity.class);
        open.putExtra(EXTRA_ID, id);
        open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent show = PendingIntent.getActivity(context, 100000 + id, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        try {
            manager.setAlarmClock(new AlarmManager.AlarmClockInfo(
                    nextTime(hour, minute, daysMask), show), fireIntent(context, id));
        } catch (SecurityException error) {
            return false;
        }
        SharedPreferences data = prefs(context);
        Set<String> ids = new HashSet<>(data.getStringSet(IDS, new HashSet<String>()));
        ids.add(String.valueOf(id));
        data.edit().putStringSet(IDS, ids)
                .putString(id + ".data", hour + "," + minute + "," + daysMask).apply();
        return true;
    }

    public static void cancel(Context context, int id) {
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (manager != null) manager.cancel(fireIntent(context, id));
        SharedPreferences data = prefs(context);
        Set<String> ids = new HashSet<>(data.getStringSet(IDS, new HashSet<String>()));
        ids.remove(String.valueOf(id));
        data.edit().putStringSet(IDS, ids).remove(id + ".data").apply();
    }

    public static void reschedule(Context context, int id) {
        String value = prefs(context).getString(id + ".data", null);
        if (value == null) return;
        try {
            String[] fields = value.split(",");
            schedule(context, id, Integer.parseInt(fields[0]),
                    Integer.parseInt(fields[1]), Integer.parseInt(fields[2]));
        } catch (IllegalArgumentException error) {
            cancel(context, id);
        }
    }

    public static void rescheduleAll(Context context) {
        Set<String> ids = new HashSet<>(prefs(context).getStringSet(IDS, new HashSet<String>()));
        for (String id : ids) {
            try { reschedule(context, Integer.parseInt(id)); }
            catch (NumberFormatException ignored) { }
        }
    }

    public static int getRingingId(Context context) {
        return prefs(context).getInt(RINGING, -1);
    }

    public static void stopRinging(Context context, int id) {
        if (getRingingId(context) != id) return;
        prefs(context).edit().remove(RINGING).commit();
        Intent stop = new Intent(context, AlarmService.class);
        stop.setAction(AlarmService.STOP);
        context.startService(stop);
    }
}
