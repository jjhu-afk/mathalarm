"""Kivy prototype for managing alarms and trying the math challenge."""

from dataclasses import replace
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from mathalarm.examples import ChallengeSession
from mathalarm.model import Alarm
from mathalarm.storage import AlarmStore


DAY_NAMES = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


class MathAlarmApp(App):
    def build(self):
        self.title = "MathAlarm"
        data_dir = Path(self.user_data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        self.store = AlarmStore(data_dir / "alarms.sqlite3")
        self.root_layout = BoxLayout(orientation="vertical", padding=12, spacing=8)
        self.show_list()
        return self.root_layout

    def on_stop(self):
        self.store.close()

    def _reset(self, title):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(
            Label(text=title, font_size="22sp", size_hint_y=None, height=48)
        )

    def show_list(self):
        self._reset("MathAlarm")
        scroll = ScrollView()
        rows = GridLayout(cols=1, spacing=6, size_hint_y=None)
        rows.bind(minimum_height=rows.setter("height"))
        alarms = self.store.list_all()
        if not alarms:
            rows.add_widget(
                Label(text="Будильников пока нет", size_hint_y=None, height=48)
            )
        for alarm in alarms:
            row = BoxLayout(size_hint_y=None, height=54, spacing=5)
            days = " ".join(
                name for index, name in enumerate(DAY_NAMES)
                if alarm.repeats_on(index)
            )
            row.add_widget(
                Label(
                    text=f"{alarm.hour:02d}:{alarm.minute:02d}  {days}",
                    size_hint_x=0.48,
                )
            )
            row.add_widget(
                Button(
                    text="Изменить",
                    size_hint_x=0.23,
                    on_release=lambda _, item=alarm: self.show_form(item),
                )
            )
            row.add_widget(
                Button(
                    text="Задачи",
                    size_hint_x=0.19,
                    on_release=lambda _, item=alarm: self.show_challenge(item),
                )
            )
            row.add_widget(
                Button(
                    text="×",
                    size_hint_x=0.10,
                    on_release=lambda _, item=alarm: self.delete_alarm(item),
                )
            )
            rows.add_widget(row)
        scroll.add_widget(rows)
        self.root_layout.add_widget(scroll)
        self.root_layout.add_widget(
            Button(
                text="Добавить будильник",
                size_hint_y=None,
                height=52,
                on_release=lambda _: self.show_form(),
            )
        )
        self.root_layout.add_widget(
            Label(
                text="Системный сигнал Android пока не подключён",
                size_hint_y=None,
                height=32,
            )
        )

    def show_form(self, alarm=None):
        self._reset("Изменить будильник" if alarm else "Новый будильник")
        time_row = BoxLayout(size_hint_y=None, height=52, spacing=8)
        hour = TextInput(
            text=f"{alarm.hour:02d}" if alarm else "07",
            input_filter="int",
            multiline=False,
            hint_text="Часы",
        )
        minute = TextInput(
            text=f"{alarm.minute:02d}" if alarm else "00",
            input_filter="int",
            multiline=False,
            hint_text="Минуты",
        )
        time_row.add_widget(hour)
        time_row.add_widget(minute)
        self.root_layout.add_widget(time_row)

        self.root_layout.add_widget(
            Label(text="Дни недели", size_hint_y=None, height=30)
        )
        days_row = BoxLayout(size_hint_y=None, height=48, spacing=4)
        day_buttons = []
        for index, name in enumerate(DAY_NAMES):
            selected = alarm.repeats_on(index) if alarm else index < 5
            button = ToggleButton(text=name, state="down" if selected else "normal")
            day_buttons.append(button)
            days_row.add_widget(button)
        self.root_layout.add_widget(days_row)

        difficulty = Spinner(
            text=str(alarm.difficulty if alarm else 1),
            values=("1", "2", "3"),
            size_hint_y=None,
            height=48,
        )
        count = TextInput(
            text=str(alarm.example_count if alarm else 3),
            input_filter="int",
            multiline=False,
            hint_text="Количество примеров от 1 до 10",
            size_hint_y=None,
            height=48,
        )
        self.root_layout.add_widget(Label(text="Сложность", size_hint_y=None, height=30))
        self.root_layout.add_widget(difficulty)
        self.root_layout.add_widget(
            Label(text="Количество примеров", size_hint_y=None, height=30)
        )
        self.root_layout.add_widget(count)
        error = Label(text="", size_hint_y=None, height=42)
        self.root_layout.add_widget(error)

        def save(_):
            try:
                mask = sum(
                    1 << index
                    for index, button in enumerate(day_buttons)
                    if button.state == "down"
                )
                values = dict(
                    hour=int(hour.text),
                    minute=int(minute.text),
                    days_mask=mask,
                    difficulty=int(difficulty.text),
                    example_count=int(count.text),
                )
                if alarm:
                    self.store.update(replace(alarm, **values))
                else:
                    self.store.add(Alarm(**values))
            except (ValueError, KeyError) as exc:
                error.text = f"Проверьте данные: {exc}"
                return
            self.show_list()

        buttons = BoxLayout(size_hint_y=None, height=52, spacing=8)
        buttons.add_widget(Button(text="Сохранить", on_release=save))
        buttons.add_widget(
            Button(text="Отмена", on_release=lambda _: self.show_list())
        )
        self.root_layout.add_widget(buttons)
        self.root_layout.add_widget(BoxLayout())

    def delete_alarm(self, alarm):
        self.store.delete(alarm.id)
        self.show_list()

    def show_challenge(self, alarm):
        self.session = ChallengeSession(alarm.difficulty, alarm.example_count)
        self._reset("Демонстрация решения примеров")
        progress = Label(size_hint_y=None, height=50)
        question = Label(font_size="30sp", size_hint_y=None, height=80)
        answer = TextInput(
            input_filter="int", multiline=False, hint_text="Ответ",
            size_hint_y=None, height=52
        )
        feedback = Label(size_hint_y=None, height=44)

        def refresh():
            progress.text = f"Решено: {self.session.solved} / {self.session.example_count}"
            question.text = (
                "Все примеры решены"
                if self.session.finished
                else self.session.current.question
            )
            answer.text = ""

        def submit(_):
            try:
                value = int(answer.text)
            except ValueError:
                feedback.text = "Введите число"
                return
            correct = self.session.submit(value)
            feedback.text = "Верно" if correct else "Неверно, попробуйте ещё"
            refresh()

        self.root_layout.add_widget(progress)
        self.root_layout.add_widget(question)
        self.root_layout.add_widget(answer)
        self.root_layout.add_widget(
            Button(
                text="Проверить",
                size_hint_y=None,
                height=52,
                on_release=submit,
            )
        )
        self.root_layout.add_widget(feedback)
        self.root_layout.add_widget(BoxLayout())
        self.root_layout.add_widget(
            Button(
                text="К списку",
                size_hint_y=None,
                height=52,
                on_release=lambda _: self.show_list(),
            )
        )
        refresh()


if __name__ == "__main__":
    MathAlarmApp().run()
