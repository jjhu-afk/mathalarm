package ru.penzgtu.mathalarm;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.media.RingtoneManager;
import android.net.Uri;
import android.os.Build;
import android.os.IBinder;

public final class AlarmService extends Service {
    static final String START = "ru.penzgtu.mathalarm.START";
    static final String STOP = "ru.penzgtu.mathalarm.STOP";
    private static final String CHANNEL = "mathalarm_alarm";
    private static final int NOTIFICATION_ID = 3181;
    private MediaPlayer player;
    private int currentId = -1;

    @Override public IBinder onBind(Intent intent) { return null; }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null) return START_NOT_STICKY;
        if (STOP.equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }
        int id = intent.getIntExtra(AlarmBridge.EXTRA_ID, -1);
        if (id < 1) return START_NOT_STICKY;
        currentId = id;
        getSharedPreferences(AlarmBridge.PREFS, MODE_PRIVATE)
                .edit().putInt(AlarmBridge.RINGING, id).commit();
        showNotification(id);
        startSound();
        return START_NOT_STICKY;
    }

    private void showNotification(int id) {
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(CHANNEL,
                    "Будильники MathAlarm", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Открыть примеры для отключения будильника");
            channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
            manager.createNotificationChannel(channel);
        }
        Intent open = new Intent(this, org.kivy.android.PythonActivity.class);
        open.putExtra(AlarmBridge.EXTRA_ID, id);
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent launch = PendingIntent.getActivity(this, 200000 + id, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL) : new Notification.Builder(this);
        builder.setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                .setContentTitle("MathAlarm — время вставать")
                .setContentText("Решите примеры, чтобы выключить сигнал")
                .setCategory(Notification.CATEGORY_ALARM)
                .setPriority(Notification.PRIORITY_MAX)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setOngoing(true)
                .setContentIntent(launch)
                .setFullScreenIntent(launch, true);
        Notification notification = builder.build();
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(NOTIFICATION_ID, notification,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK);
        } else {
            startForeground(NOTIFICATION_ID, notification);
        }
    }

    private void startSound() {
        releaseSound();
        Uri uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
        if (uri == null) uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
        if (uri == null) return;
        try {
            player = new MediaPlayer();
            player.setAudioAttributes(new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build());
            player.setDataSource(this, uri);
            player.setLooping(true);
            player.prepare();
            player.start();
        } catch (Exception error) {
            releaseSound();
        }
    }

    private void releaseSound() {
        if (player != null) {
            try { player.stop(); } catch (IllegalStateException ignored) { }
            player.release();
            player = null;
        }
    }

    @Override public void onDestroy() {
        releaseSound();
        if (AlarmBridge.getRingingId(this) == currentId) {
            getSharedPreferences(AlarmBridge.PREFS, MODE_PRIVATE)
                    .edit().remove(AlarmBridge.RINGING).apply();
        }
        super.onDestroy();
    }
}
