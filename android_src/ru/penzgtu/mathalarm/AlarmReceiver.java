package ru.penzgtu.mathalarm;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public final class AlarmReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        int id = intent.getIntExtra(AlarmBridge.EXTRA_ID, -1);
        if (id < 1) return;
        AlarmBridge.reschedule(context, id);
        Intent start = new Intent(context, AlarmService.class);
        start.setAction(AlarmService.START);
        start.putExtra(AlarmBridge.EXTRA_ID, id);
        if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(start);
        else context.startService(start);
    }
}
