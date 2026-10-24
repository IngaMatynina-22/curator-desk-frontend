from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AppError

from gui.gateway import call, user_message
from gui.ui.icons import icon
from gui.ui.widgets.error_banner import ErrorBanner
from gui.ui.widgets.page_scroll import PageScroll
from gui.ui.widgets.simple_charts import BarChartWidget

if TYPE_CHECKING:
    from gui.gateway import BackendGateway
    from gui.ui.widgets.toast import ToastManager


class AnalyticsPage(QWidget):
    def __init__(self, gateway: BackendGateway, *, toast: ToastManager | None = None, parent=None):
        super().__init__(parent)
        self.gateway = gateway
        self.toast = toast

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = PageScroll()
        outer.addWidget(scroll)
        root = scroll.body_layout
        root.setSpacing(16)
        row = QHBoxLayout()
        title = QLabel("Аналітика")
        title.setObjectName("pageTitle")
        row.addWidget(title)
        row.addStretch()
        refresh = QPushButton("Оновити")
        refresh.setObjectName("ghostButton")
        refresh.clicked.connect(self.reload)
        row.addWidget(refresh)
        root.addLayout(row)

        self.error = ErrorBanner()
        root.addWidget(self.error)

        self.kpi = QGridLayout()
        self.kpi.setSpacing(12)
        self.ov_labels: dict[str, QLabel] = {}
        for i, (key, caption, ikey) in enumerate(
            [
                ("students", "Студентів", "users"),
                ("absences", "Пропусків", "attendance"),
                ("assignments_open", "Прострочені доручення", "overdue"),
                ("events", "Заходів", "calendar"),
            ]
        ):
            box = QFrame()
            box.setObjectName("kpiPanel")
            lay = QHBoxLayout(box)
            lay.setContentsMargins(14, 12, 14, 12)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon(ikey, color="#1A7A6D", size=24).pixmap(24, 24))
            lay.addWidget(icon_lbl)
            col = QVBoxLayout()
            cap = QLabel(caption)
            cap.setObjectName("kpiCaption")
            val = QLabel("—")
            val.setObjectName("kpiValue")
            col.addWidget(cap)
            col.addWidget(val)
            lay.addLayout(col)
            self.ov_labels[key] = val
            self.kpi.addWidget(box, 0, i)
        root.addLayout(self.kpi)

        overdue_box = QFrame()
        overdue_box.setObjectName("kpiPanel")
        ob_lay = QVBoxLayout(overdue_box)
        ob_lay.setContentsMargins(16, 12, 16, 12)
        self.overdue_lbl = QLabel("Прострочені доручення: —")
        self.overdue_lbl.setObjectName("pageTitle")
        self.overdue_lbl.setStyleSheet("font-size: 16px;")
        ob_lay.addWidget(self.overdue_lbl)
        root.addWidget(overdue_box)

        chart_head = QLabel("Тренд відвідуваності")
        chart_head.setObjectName("pageTitle")
        chart_head.setStyleSheet("font-size: 16px;")
        root.addWidget(chart_head)
        self.chart = BarChartWidget()
        self.chart.setMinimumHeight(220)
        root.addWidget(self.chart)

        act_head = QLabel("Активність")
        act_head.setObjectName("pageTitle")
        act_head.setStyleSheet("font-size: 16px;")
        root.addWidget(act_head)
        self.activity = QLabel("—")
        self.activity.setObjectName("mutedLabel")
        self.activity.setWordWrap(True)
        root.addWidget(self.activity)

    def refresh(self) -> None:
        self.reload()

    def reload(self) -> None:
        self.error.clear()
        try:
            overview = call(self.gateway.c.statistics.overview)
            self.ov_labels["students"].setText(str(overview.students_active))
            self.ov_labels["absences"].setText(str(overview.absences))
            self.ov_labels["assignments_open"].setText(str(overview.assignments_overdue))
            self.ov_labels["events"].setText(str(overview.events_planned))

            overdue = call(self.gateway.c.statistics.get_overdue_summary)
            count = int(overdue.overdue_count)
            self.overdue_lbl.setText(f"Прострочені доручення: {count}")

            points = call(self.gateway.c.statistics.get_attendance_trend, "week")
            labels = [str(p.bucket) for p in points]
            absences = [float(p.absences) for p in points]
            present = [float(p.present) for p in points]
            self.chart.set_data(
                labels,
                [
                    ("Пропуски", absences, "#9B2C2C"),
                    ("Присутні", present, "#1A7A6D"),
                ],
            )

            activity = call(self.gateway.c.statistics.get_activity_summary)
            self.activity.setText(
                f"Заходи: {activity.events_planned}/{activity.events_completed}; "
                f"Зустрічі: {activity.meetings_planned}/{activity.meetings_completed}; "
                f"Чергування: {activity.duties_planned}/{activity.duties_done}"
            )
        except AppError as exc:
            self.error.show_error(user_message(exc))
