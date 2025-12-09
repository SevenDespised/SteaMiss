from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class ToolManager:
    def __init__(self):
        self.active_tools = {}

    def open_tool(self, tool_name):
        """
        打开指定的工具，如果已打开则激活
        """
        if tool_name in self.active_tools:
            window = self.active_tools[tool_name]
            window.show()
            window.activateWindow()
            return

        # 工厂模式：根据名字创建对应的工具窗口
        new_tool = None
        if tool_name == "memo":
            new_tool = self.create_memo_window()
        elif tool_name == "alarm":
            new_tool = self.create_alarm_window()
            
        if new_tool:
            self.active_tools[tool_name] = new_tool
            new_tool.show()

    def create_memo_window(self):
        # 示例：简单的备忘录窗口
        w = QWidget()
        w.setWindowTitle("备忘录")
        w.resize(300, 200)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("这是一个备忘录示例"))
        w.setLayout(layout)
        return w

    def create_alarm_window(self):
        # 示例：简单的闹钟窗口
        w = QWidget()
        w.setWindowTitle("闹钟")
        w.resize(200, 100)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("这是一个闹钟示例"))
        w.setLayout(layout)
        return w
