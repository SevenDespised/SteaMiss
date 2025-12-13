from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget
)
from PyQt6.QtCore import Qt


class ReminderSettingsDialog(QDialog):
    """
    提醒设置对话框
    负责收集结束时间、提醒间隔、提醒后暂停间隔三个参数。
    """

    def __init__(self, timer_handler, parent=None):
        super().__init__(parent)
        self.timer_handler = timer_handler
        self.setWindowTitle("提醒设置")
        self.setModal(True)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        # 结束时间
        self.enable_end = QCheckBox("启用")
        end_label = QLabel("结束时间")
        end_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        end_label_widget = self._wrap_label_with_enable(self.enable_end, end_label)
        self.end_h, self.end_m, self.end_s = self._create_time_inputs(99, "结束时间")
        end_inputs = self._wrap_time_row(self.end_h, self.end_m, self.end_s)
        form.addRow(end_label_widget, end_inputs)
        self._bind_enable(self.enable_end, [self.end_h, self.end_m, self.end_s])

        # 提醒间隔 (时分秒)
        self.remind_h, self.remind_m, self.remind_s = self._create_time_inputs(99, "提醒间隔")
        self.enable_remind = QCheckBox("启用")
        remind_label = QLabel("提醒间隔")
        remind_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        remind_label_widget = self._wrap_label_with_enable(self.enable_remind, remind_label)
        form.addRow(remind_label_widget, self._wrap_time_row(self.remind_h, self.remind_m, self.remind_s))
        self._bind_enable(self.enable_remind, [self.remind_h, self.remind_m, self.remind_s])
        self.enable_remind.toggled.connect(self._on_remind_toggled)

        # 提醒后暂停 (时分秒)
        self.pause_h, self.pause_m, self.pause_s = self._create_time_inputs(99, "提醒后暂停")
        self.enable_pause = QCheckBox("启用")
        pause_label = QLabel("提醒后暂停")
        pause_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        pause_label_widget = self._wrap_label_with_enable(self.enable_pause, pause_label)
        form.addRow(pause_label_widget, self._wrap_time_row(self.pause_h, self.pause_m, self.pause_s))
        self._bind_enable(self.enable_pause, [self.pause_h, self.pause_m, self.pause_s])

        layout.addLayout(form)

        # 预设行
        presets_row = QHBoxLayout()
        presets_row.setContentsMargins(0, 0, 0, 0)
        presets_row.setSpacing(8)
        self.preset_combo = QComboBox()
        self.btn_apply_preset = QPushButton("应用预设")
        self.btn_save_preset = QPushButton("保存为预设")
        self.btn_delete_preset = QPushButton("删除预设")
        self.btn_apply_preset.clicked.connect(self._on_apply_preset)
        self.btn_save_preset.clicked.connect(self._on_save_preset)
        self.btn_delete_preset.clicked.connect(self._on_delete_preset)
        presets_row.addWidget(self.preset_combo, 1)
        presets_row.addWidget(self.btn_apply_preset)
        presets_row.addWidget(self.btn_save_preset)
        presets_row.addWidget(self.btn_delete_preset)
        layout.addLayout(presets_row)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _load_values(self):
        settings = self.timer_handler.get_reminder_settings() if self.timer_handler else {}
        end_seconds = settings.get("timer_end_seconds")
        if end_seconds is None:
            self.enable_end.setChecked(False)
        else:
            hours = end_seconds // 3600
            minutes = (end_seconds % 3600) // 60
            seconds = end_seconds % 60
            self.end_h.setValue(int(hours))
            self.end_m.setValue(int(minutes))
            self.end_s.setValue(int(seconds))
            self.enable_end.setChecked(True)

        remind_seconds = int(settings.get("timer_remind_interval_seconds", 0))
        rh, rm, rs = self._sec_to_hms(remind_seconds)
        self.remind_h.setValue(rh)
        self.remind_m.setValue(rm)
        self.remind_s.setValue(rs)
        self.enable_remind.setChecked(remind_seconds > 0)

        pause_seconds = int(settings.get("timer_pause_after_remind_seconds", 0))
        ph, pm, ps = self._sec_to_hms(pause_seconds)
        self.pause_h.setValue(ph)
        self.pause_m.setValue(pm)
        self.pause_s.setValue(ps)
        self.enable_pause.setChecked(pause_seconds > 0)

        self._apply_enable_states()
        self._refresh_presets()

    def _on_accept(self):
        end_seconds, remind_interval_seconds, pause_after_seconds = self._collect_settings()

        if self.timer_handler:
            self.timer_handler.update_reminder_settings(
                end_seconds=end_seconds,
                remind_interval_seconds=remind_interval_seconds,
                pause_after_remind_seconds=pause_after_seconds
            )
        self.accept()

    # --- 工具方法 ---
    def _create_time_inputs(self, max_hour, name):
        """
        创建时分秒输入框
        @param max_hour: 小时上限
        @param name: 用于占位的名称（未使用，仅保留接口）
        """
        h = QSpinBox()
        h.setRange(0, max_hour)
        h.setSuffix(" 小时")
        m = QSpinBox()
        m.setRange(0, 59)
        m.setSuffix(" 分")
        s = QSpinBox()
        s.setRange(0, 59)
        s.setSuffix(" 秒")
        return h, m, s

    def _wrap_time_row(self, h, m, s):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(h)
        row.addWidget(m)
        row.addWidget(s)
        widget = QWidget()
        widget.setLayout(row)
        return widget

    def _wrap_label_with_enable(self, checkbox, label_widget):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(checkbox)
        row.addWidget(label_widget)
        wrapper = QWidget()
        wrapper.setLayout(row)
        return wrapper

    def _bind_enable(self, checkbox, widgets):
        checkbox.toggled.connect(lambda checked: self._set_widgets_enabled(widgets, checked))

    def _set_widgets_enabled(self, widgets, enabled):
        for w in widgets:
            w.setEnabled(enabled)

    def _apply_enable_states(self):
        self._set_widgets_enabled([self.end_h, self.end_m, self.end_s], self.enable_end.isChecked())
        self._set_widgets_enabled([self.remind_h, self.remind_m, self.remind_s], self.enable_remind.isChecked())
        self.enable_pause.setEnabled(self.enable_remind.isChecked())
        self._set_widgets_enabled([self.pause_h, self.pause_m, self.pause_s], self.enable_pause.isChecked())

    def _on_remind_toggled(self, checked):
        if not checked:
            self.enable_pause.setChecked(False)
        self._apply_enable_states()

    def _collect_settings(self):
        end_seconds = None
        if self.enable_end.isChecked():
            end_seconds = self._hms_to_sec(self.end_h, self.end_m, self.end_s)
            if end_seconds <= 0:
                end_seconds = None

        remind_interval_seconds = 0
        if self.enable_remind.isChecked():
            remind_interval_seconds = self._hms_to_sec(self.remind_h, self.remind_m, self.remind_s)

        pause_after_seconds = 0
        if self.enable_pause.isChecked():
            pause_after_seconds = self._hms_to_sec(self.pause_h, self.pause_m, self.pause_s)

        return end_seconds, remind_interval_seconds, pause_after_seconds

    def _collect_preset_data(self):
        end_seconds, remind_interval_seconds, pause_after_seconds = self._collect_settings()
        return {
            "end_enabled": self.enable_end.isChecked(),
            "end_seconds": end_seconds,
            "remind_enabled": self.enable_remind.isChecked(),
            "remind_seconds": remind_interval_seconds,
            "pause_enabled": self.enable_pause.isChecked(),
            "pause_seconds": pause_after_seconds
        }

    def _apply_preset_data(self, preset):
        if not preset:
            return
        self.enable_end.setChecked(bool(preset.get("end_enabled")))
        end_seconds = preset.get("end_seconds")
        if end_seconds is not None:
            eh, em, es = self._sec_to_hms(end_seconds)
            self.end_h.setValue(eh)
            self.end_m.setValue(em)
            self.end_s.setValue(es)

        self.enable_remind.setChecked(bool(preset.get("remind_enabled")))
        remind_seconds = preset.get("remind_seconds", 0) or 0
        rh, rm, rs = self._sec_to_hms(remind_seconds)
        self.remind_h.setValue(rh)
        self.remind_m.setValue(rm)
        self.remind_s.setValue(rs)

        self.enable_pause.setChecked(bool(preset.get("pause_enabled")) and self.enable_remind.isChecked())
        pause_seconds = preset.get("pause_seconds", 0) or 0
        ph, pm, ps = self._sec_to_hms(pause_seconds)
        self.pause_h.setValue(ph)
        self.pause_m.setValue(pm)
        self.pause_s.setValue(ps)

        self._apply_enable_states()

    def _refresh_presets(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        presets = self.timer_handler.get_presets() if self.timer_handler else []
        for p in presets:
            name = p.get("name")
            if name:
                self.preset_combo.addItem(name)
        self.preset_combo.blockSignals(False)

    def _on_apply_preset(self):
        name = self.preset_combo.currentText().strip()
        if not name or not self.timer_handler:
            return
        preset = self.timer_handler.load_preset(name)
        self._apply_preset_data(preset)

    def _on_save_preset(self):
        if not self.timer_handler:
            return
        presets = self.timer_handler.get_presets()
        default_name = f"预设{len(presets) + 1}"
        name, ok = QInputDialog.getText(self, "保存预设", "预设名称：", text=default_name)
        if not ok:
            return
        name = name.strip()
        if not name:
            return
        data = self._collect_preset_data()
        self.timer_handler.save_preset(name, data)
        self._refresh_presets()
        index = self.preset_combo.findText(name)
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)

    def _on_delete_preset(self):
        if not self.timer_handler:
            return
        name = self.preset_combo.currentText().strip()
        if not name:
            return
        confirm = QMessageBox.question(
            self,
            "删除预设",
            f"确定删除预设「{name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.timer_handler.delete_preset(name)
        self._refresh_presets()
        # 选中第一项（若存在）
        if self.preset_combo.count() > 0:
            self.preset_combo.setCurrentIndex(0)

    def _sec_to_hms(self, seconds):
        seconds = max(0, int(seconds or 0))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return h, m, s

    def _hms_to_sec(self, h_spin, m_spin, s_spin):
        return h_spin.value() * 3600 + m_spin.value() * 60 + s_spin.value()

