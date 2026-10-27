package ru.penzgtu.mathalarm.model

/** Доменная модель будильника для первого релиза. */
data class Alarm(
    val id: Long,
    val hour: Int,
    val minute: Int,
    val daysMask: Int,
    val enabled: Boolean,
    val difficulty: Int,
    val exampleCount: Int
) {
    init {
        require(hour in 0..23)
        require(minute in 0..59)
        require(daysMask in 1..127)
        require(difficulty in 1..3)
        require(exampleCount in 1..10)
    }
}
