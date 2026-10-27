package ru.penzgtu.mathalarm.scheduler

import ru.penzgtu.mathalarm.model.Alarm

/** Граница между доменной логикой и механизмом точных будильников Android. */
interface AlarmScheduler {
    fun schedule(alarm: Alarm)
    fun cancel(alarmId: Long)
    fun rescheduleEnabled(alarms: List<Alarm>)
}
