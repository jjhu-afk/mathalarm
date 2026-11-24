"""MathAlarm: Android alarm clock with arithmetic dismissal."""
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from mathalarm.android import AndroidAlarms
from mathalarm.examples import ChallengeSession
from mathalarm.model import Alarm
from mathalarm.schedule import next_occurrence
from mathalarm.storage import AlarmStore

DAY_NAMES = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
BG = (0.055, 0.075, 0.12, 1)
CARD = (0.11, 0.145, 0.21, 1)
ACCENT = (0.18, 0.79, 0.73, 1)
TEXT = (0.96, 0.98, 1, 1)
MUTED = (0.67, 0.73, 0.79, 1)
RED = (1, 0.43, 0.43, 1)


def label(text, height=36, size=16, color=TEXT, bold=False):
    item = Label(text=text, color=color, font_size=f"{size}sp", bold=bold,
                 size_hint_y=None, height=dp(height), halign="left", valign="middle")
    item.bind(size=lambda widget, _: setattr(widget, "text_size", (widget.width, None)))
    return item


def button(text, callback, height=52, primary=False, width=None):
    item = Button(text=text, font_size="16sp", bold=primary,
                  size_hint_y=None, height=dp(height), background_normal="",
                  background_down="", background_color=ACCENT if primary else CARD,
                  color=BG if primary else TEXT)
    if width is not None:
        item.size_hint_x, item.width = None, dp(width)
    item.bind(on_release=callback)
    return item


def input_field(value, hint):
    return TextInput(text=value, hint_text=hint, multiline=False,
                     input_filter="int", font_size="22sp", halign="center",
                     size_hint_y=None, height=dp(56), background_color=CARD,
                     foreground_color=TEXT, hint_text_color=MUTED,
                     cursor_color=ACCENT, padding=[dp(10), dp(12)])


class MathAlarmApp(App):
    def build(self):
        self.title = "MathAlarm"
        Window.clearcolor = BG
        Window.softinput_mode = "below_target"
        data_dir = Path(self.user_data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        self.store = AlarmStore(data_dir / "alarms.sqlite3")
        self.android = AndroidAlarms()
        self.active_alarm_id = None
        self.root_layout = BoxLayout(orientation="vertical", spacing=dp(12),
                                     padding=[dp(16)] * 4)
        Window.bind(on_keyboard=self._on_keyboard)
        self.show_list()
        Clock.schedule_once(self._apply_insets, 0.3)
        return self.root_layout

    def on_start(self):
        if self.android.available:
            try:
                from jnius import autoclass
                if autoclass("android.os.Build$VERSION").SDK_INT >= 33:
                    self.android.request_notifications()
                self._sync_all()
                from android import activity
                activity.bind(on_new_intent=self._on_new_intent)
                Clock.schedule_once(self._check_ringing, 0.5)
            except Exception as error:
                self._notice("Не удалось подключить системный будильник: " + str(error))

    def on_resume(self):
        Clock.schedule_once(self._apply_insets, 0.1)
        Clock.schedule_once(self._check_ringing, 0.2)
        self._sync_all()
        return True

    def on_stop(self):
        self.store.close()

    def _apply_insets(self, _):
        try:
            top, bottom = self.android.system_insets()
            self.root_layout.padding = [dp(16), dp(16) + top,
                                        dp(16), dp(16) + bottom]
        except Exception:
            if self.android.available:
                self.root_layout.padding = [dp(16), dp(40), dp(16), dp(72)]

    def _on_keyboard(self, _, key, *__):
        return bool(key == 27 and self.active_alarm_id is not None)

    def _on_new_intent(self, intent):
        Clock.schedule_once(self._check_ringing, 0)

    def _check_ringing(self, _):
        incoming = self.android.current_intent_id()
        ringing = self.android.ringing_id()
        alarm_id = ringing if ringing > 0 else incoming
        if alarm_id < 1 or alarm_id == self.active_alarm_id:
            return
        alarm = self.store.get(alarm_id)
        if alarm is not None:
            self.show_challenge(alarm, active=True)

    def _sync_all(self):
        if not self.android.available:
            return
        for alarm in self.store.list_all():
            if alarm.enabled:
                self.android.schedule(alarm)
            else:
                self.android.cancel(alarm.id)

    def _notice(self, message):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(label(message, 100, 15))
        popup = Popup(title="MathAlarm", content=content,
                      size_hint=(0.88, None), height=dp(220))
        content.add_widget(button("Понятно", lambda _: popup.dismiss(), primary=True))
        popup.open()

    def _reset(self, title, subtitle=None):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(label(title, 48, 28, TEXT, True))
        if subtitle:
            self.root_layout.add_widget(label(subtitle, 36, 15, MUTED))

    def show_list(self):
        self.active_alarm_id = None
        self._reset("MathAlarm", "Будильник с задачами")
        if self.android.available and not self.android.can_schedule():
            self.root_layout.add_widget(label(
                "Разрешите точные будильники в настройках Android", 54, 14, RED))
            self.root_layout.add_widget(button(
                "Открыть настройки будильников", self._open_alarm_settings, 46))
        scroll = ScrollView(do_scroll_x=False)
        rows = GridLayout(cols=1, spacing=dp(12), size_hint_y=None)
        rows.bind(minimum_height=rows.setter("height"))
        alarms = self.store.list_all()
        if not alarms:
            empty = BoxLayout(orientation="vertical", padding=dp(20),
                              spacing=dp(8), size_hint_y=None, height=dp(170))
            empty.add_widget(label("Пока нет будильников", 52, 22, TEXT, True))
            empty.add_widget(label(
                "Нажмите кнопку ниже, выберите время и дни, затем сохраните.",
                80, 16, MUTED))
            rows.add_widget(empty)
        for alarm in alarms:
            card = BoxLayout(orientation="vertical", padding=dp(12),
                             spacing=dp(6), size_hint_y=None, height=dp(190))
            with card.canvas.before:
                Color(*CARD)
                shape = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
            card.bind(pos=lambda w, _, s=shape: setattr(s, "pos", w.pos),
                      size=lambda w, _, s=shape: setattr(s, "size", w.size))
            head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            head.add_widget(label(f"{alarm.hour:02d}:{alarm.minute:02d}", 48, 30,
                                  TEXT if alarm.enabled else MUTED, True))
            head.add_widget(button("Вкл" if alarm.enabled else "Выкл",
                                   lambda _, a=alarm: self.toggle_alarm(a),
                                   42, primary=alarm.enabled, width=78))
            card.add_widget(head)
            days = " ".join(name for i, name in enumerate(DAY_NAMES) if alarm.repeats_on(i))
            card.add_widget(label(days, 25, 15, MUTED))
            status = ("Следующий: " + next_occurrence(alarm, datetime.now()).strftime("%d.%m %H:%M")
                      if alarm.enabled else "Будильник выключен")
            card.add_widget(label(status, 25, 14, MUTED))
            actions = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
            actions.add_widget(button("Изменить", lambda _, a=alarm: self.show_form(a), 38))
            actions.add_widget(button("Проба", lambda _, a=alarm: self.show_challenge(a), 38))
            actions.add_widget(button("Удалить", lambda _, a=alarm: self.delete_alarm(a), 38))
            card.add_widget(actions)
            rows.add_widget(card)
        scroll.add_widget(rows)
        self.root_layout.add_widget(scroll)
        self.root_layout.add_widget(button("+  Добавить будильник",
                                           lambda _: self.show_form(), 58, True))

    def show_form(self, alarm=None):
        self._reset("Изменить будильник" if alarm else "Новый будильник")
        scroll = ScrollView(do_scroll_x=False)
        form = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        form.add_widget(label("Время", 34, 18, TEXT, True))
        time_row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(12))
        hour = input_field(f"{alarm.hour:02d}" if alarm else "07", "Часы 0–23")
        minute = input_field(f"{alarm.minute:02d}" if alarm else "00", "Минуты 0–59")
        time_row.add_widget(hour)
        time_row.add_widget(label(":", 56, 26))
        time_row.add_widget(minute)
        form.add_widget(time_row)
        form.add_widget(label("Часы (0–23)                  Минуты (0–59)", 28, 13, MUTED))
        form.add_widget(label("Дни повторения", 34, 18, TEXT, True))
        days_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(3))
        day_buttons = []
        for i, name in enumerate(DAY_NAMES):
            selected = alarm.repeats_on(i) if alarm else True
            day = ToggleButton(text=name, state="down" if selected else "normal",
                               background_color=CARD, color=TEXT, font_size="14sp")
            day_buttons.append(day)
            days_row.add_widget(day)
        form.add_widget(days_row)

        def test_time(_):
            value = datetime.now() + timedelta(minutes=2)
            hour.text, minute.text = str(value.hour), str(value.minute)
            for day in day_buttons:
                day.state = "down"

        form.add_widget(button("Проверить: поставить через 2 минуты", test_time, 46))
        form.add_widget(label("Сложность примеров", 34, 18, TEXT, True))
        difficulty = Spinner(text=str(alarm.difficulty if alarm else 1),
                             values=("1", "2", "3"), size_hint_y=None,
                             height=dp(52), background_color=CARD, color=TEXT)
        form.add_widget(difficulty)
        form.add_widget(label("1 — легко, 2 — средне, 3 — сложно", 28, 14, MUTED))
        form.add_widget(label("Сколько примеров решить (1–10)", 34, 18, TEXT, True))
        count = input_field(str(alarm.example_count if alarm else 3), "От 1 до 10")
        form.add_widget(count)
        error = label("", 44, 14, RED)
        form.add_widget(error)
        scroll.add_widget(form)
        self.root_layout.add_widget(scroll)

        def save(_):
            try:
                mask = sum(1 << i for i, day in enumerate(day_buttons) if day.state == "down")
                values = dict(hour=int(hour.text), minute=int(minute.text),
                              days_mask=mask, difficulty=int(difficulty.text),
                              example_count=int(count.text))
                saved = replace(alarm, **values) if alarm else Alarm(**values)
                if alarm:
                    self.store.update(saved)
                else:
                    saved = self.store.add(saved)
                scheduled = True
                if saved.enabled:
                    scheduled = self.android.schedule(saved)
                else:
                    self.android.cancel(saved.id)
                if not scheduled and self.android.available:
                    self.store.update(replace(saved, enabled=False))
            except (ValueError, KeyError) as exc:
                error.text = "Проверьте время, дни и количество. " + str(exc)
                return
            self.show_list()
            if not scheduled and self.android.available:
                self._notice("Сохранено выключенным. Разрешите точные будильники "
                             "в настройках Android и включите его.")

        footer = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        footer.add_widget(button("Отмена", lambda _: self.show_list(), 56))
        footer.add_widget(button("Сохранить", save, 56, True))
        self.root_layout.add_widget(footer)

    def toggle_alarm(self, alarm):
        changed = replace(alarm, enabled=not alarm.enabled)
        if changed.enabled and not self.android.schedule(changed) and self.android.available:
            self._notice("Не удалось включить: разрешите точные будильники "
                         "в настройках Android.")
            return
        if not changed.enabled:
            self.android.cancel(alarm.id)
        self.store.update(changed)
        self.show_list()

    def _open_alarm_settings(self, _):
        try:
            self.android.open_alarm_settings()
        except Exception:
            self._notice("Откройте настройки приложения MathAlarm и разрешите "
                         "точные будильники.")

    def delete_alarm(self, alarm):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        content.add_widget(label(f"Удалить будильник {alarm.hour:02d}:{alarm.minute:02d}?", 80, 18))
        popup = Popup(title="Удаление", content=content,
                      size_hint=(0.88, None), height=dp(220))

        def confirm(_):
            self.android.cancel(alarm.id)
            self.store.delete(alarm.id)
            popup.dismiss()
            self.show_list()

        actions = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        actions.add_widget(button("Отмена", lambda _: popup.dismiss()))
        actions.add_widget(button("Удалить", confirm, primary=True))
        content.add_widget(actions)
        popup.open()

    def show_challenge(self, alarm, active=False):
        self.active_alarm_id = alarm.id if active else None
        self.session = ChallengeSession(alarm.difficulty, alarm.example_count)
        self._reset("Будильник звонит" if active else "Проба примеров",
                    "Решите все примеры, чтобы выключить сигнал" if active
                    else "Проверка без сигнала")
        progress = label("", 48, 18, MUTED)
        question = label("", 110, 36, TEXT, True)
        answer = input_field("", "Введите ответ")
        feedback = label("", 52, 16, RED)
        self.root_layout.add_widget(progress)
        self.root_layout.add_widget(question)
        self.root_layout.add_widget(answer)
        self.root_layout.add_widget(feedback)

        def refresh():
            progress.text = f"Решено: {self.session.solved} из {self.session.example_count}"
            question.text = "Готово!" if self.session.finished else self.session.current.question
            answer.text = ""

        def submit(_):
            try:
                value = int(answer.text)
            except ValueError:
                feedback.text = "Введите число"
                return
            correct = self.session.submit(value)
            feedback.text = "Верно" if correct else "Неверно, попробуйте ещё"
            if self.session.finished:
                if active:
                    self.android.stop(alarm.id)
                self.show_list()
            else:
                refresh()

        answer.bind(on_text_validate=submit)
        self.root_layout.add_widget(button("Проверить ответ", submit, 58, True))
        self.root_layout.add_widget(BoxLayout())
        if not active:
            self.root_layout.add_widget(button("К списку", lambda _: self.show_list()))
        refresh()


if __name__ == "__main__":
    MathAlarmApp().run()
