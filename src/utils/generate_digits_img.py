import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QLinearGradient, QImage

class SevenSegmentDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 窗口设置
        self.setWindowTitle('增强版7段数码管 (0-9)')
        self.setFixedSize(900, 250)  # 适配加粗后的数字尺寸
        self.setStyleSheet('background-color: #1a1a1a;')  # 深色背景更突出数码管

    def draw_single_digit(self, painter, x, y, w, h, digit, main_color, highlight_color, draw_label=True):
        """
        绘制加粗带弧形和高亮的7段数码管数字
        :param painter: QPainter对象
        :param x: 数字左上角x坐标
        :param y: 数字左上角y坐标
        :param w: 数字整体宽度
        :param h: 数字整体高度
        :param digit: 要绘制的数字(0-9)
        :param main_color: 数码管主体颜色
        :param highlight_color: 高亮颜色
        """
        # 7段定义：a(上), b(右上), c(右下), d(下), e(左下), f(左上), g(中)
        segment_map = {
            0: (1, 1, 1, 1, 1, 1, 0),
            1: (0, 1, 1, 0, 0, 0, 0),
            2: (1, 1, 0, 1, 1, 0, 1),
            3: (1, 1, 1, 1, 0, 0, 1),
            4: (0, 1, 1, 0, 0, 1, 1),
            5: (1, 0, 1, 1, 0, 1, 1),
            6: (1, 0, 1, 1, 1, 1, 1),
            7: (1, 1, 1, 0, 0, 0, 0),
            8: (1, 1, 1, 1, 1, 1, 1),
            9: (1, 1, 1, 1, 0, 1, 1)
        }

        # --- 动态计算尺寸 ---
        # 定义比例因子
        thickness_factor = 0.15  # 笔画粗细占宽度的比例
        
        seg_width = w * thickness_factor          # 段的粗细
        spacing = seg_width * 0.03               # 间隙
        
        # 根据总宽总高反推段长
        horz_seg_length = w - 2 * seg_width - 2 * spacing
        vert_seg_length = (h - 3 * seg_width - 4 * spacing) / 2
        
        round_radius = seg_width * 0.4    # 圆角半径

        # 验证数字范围
        if digit not in segment_map:
            return

        segments = segment_map[digit]
        painter.setPen(Qt.PenStyle.NoPen)  # 无轮廓

        # 定义熄灭状态的颜色 (深灰色，低透明度)
        off_color = QColor(100, 100, 100, 80)

        # 绘制单段的通用函数（主体+高亮）
        def draw_segment(rect_x, rect_y, rect_w, rect_h, is_active, is_horizontal=True):
            # 1. 确定颜色
            if is_active:
                current_main_color = main_color
            else:
                current_main_color = off_color

            # 2. 绘制数码管主体（带弧形）
            painter.setBrush(QColor(current_main_color))
            painter.drawRoundedRect(
                int(rect_x), int(rect_y), int(rect_w), int(rect_h),
                round_radius, round_radius
            )
            
            # 3. 绘制高亮（仅当激活时绘制）
            if is_active:
                painter.setBrush(QColor(highlight_color))
                if is_horizontal:
                    # 横向段：高亮在上方
                    highlight_rect = (
                        int(rect_x + 2), int(rect_y + 1),
                        int(rect_w - 4), int(rect_h // 2 - 2)
                    )
                else:
                    # 纵向段：高亮在左侧
                    highlight_rect = (
                        int(rect_x + 1), int(rect_y + 2),
                        int(rect_w // 2 - 2), int(rect_h - 4)
                    )
                painter.drawRoundedRect(
                    *highlight_rect,
                    round_radius // 2, round_radius // 2
                )

        # --- 绘制各段（按7段布局）---
        # 坐标计算辅助变量
        left_x = x
        right_x = x + seg_width + horz_seg_length + spacing * 2
        mid_x = x + seg_width + spacing
        
        top_y = y
        mid_y = y + seg_width + vert_seg_length + spacing * 2
        bottom_y = y + (seg_width + vert_seg_length + spacing * 2) * 2

        # a: 顶部横段
        draw_segment(mid_x, top_y, horz_seg_length, seg_width, segments[0], True)

        # b: 右上竖段
        draw_segment(right_x, top_y + seg_width + spacing, seg_width, vert_seg_length, segments[1], False)

        # c: 右下竖段
        draw_segment(right_x, mid_y + seg_width + spacing, seg_width, vert_seg_length, segments[2], False)

        # d: 底部横段
        draw_segment(mid_x, bottom_y, horz_seg_length, seg_width, segments[3], True)

        # e: 左下竖段
        draw_segment(left_x, mid_y + seg_width + spacing, seg_width, vert_seg_length, segments[4], False)

        # f: 左上竖段
        draw_segment(left_x, top_y + seg_width + spacing, seg_width, vert_seg_length, segments[5], False)

        # g: 中间横段
        draw_segment(mid_x, mid_y, horz_seg_length, seg_width, segments[6], True)

        # 绘制数字标签（白色小字）
        if draw_label:
            painter.setPen(QColor(200, 200, 200))
            text_y = y + h + 15
            painter.drawText(int(x + w/2 - 3), int(text_y), str(digit))

    def paintEvent(self, event):
        painter = QPainter(self)
        # 关闭抗锯齿，保留数码管硬朗质感（如需更平滑可开启）
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 基础配置
        start_x = 40          # 第一个数字的x起始坐标
        start_y = 50          # 数字y起始坐标
        digit_w = 50          # 单个数字宽度
        digit_h = 90          # 单个数字高度
        digit_spacing = 150    # 数字之间的间距 (起始点间距)
        
        # ******** 修改1：数字主体色改为深红色 ********
        main_color = "#000000"    # 深红色（原橙红色 #FF7A00）
        # ******** 修改2：高亮色改为浅红色（适配深红色主体）********
        highlight_color = "#666666"  # 浅粉红（原浅橙黄 #FFE0B2）
        for i in range(10):
            # 分别绘制0-9并保存
            digit_x = start_x + i * digit_spacing
            # 设置高亮色的透明度（50%）
            highlight = QColor(highlight_color)
            highlight.setAlpha(128)
            self.draw_single_digit(painter, digit_x, start_y, 100, 170, i, main_color, highlight)


def export_digits(output_dir="digits", digit_w=120, digit_h=200, main_color="#C70039", highlight_color="#FFC0CB"):
    """离屏渲染0-9并保存为PNG。"""
    os.makedirs(output_dir, exist_ok=True)

    widget = SevenSegmentDisplay()
    for i in range(10):
        # 创建透明画布
        img = QImage(digit_w + 20, digit_h + 20, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        highlight = QColor(highlight_color)
        highlight.setAlpha(128)

        # 在带边距的画布中绘制，避免裁剪
        widget.draw_single_digit(painter, 10, 10, digit_w, digit_h, i, main_color, highlight, draw_label=False)
        painter.end()

        img.save(os.path.join(output_dir, f"{i}.png"))


def draw_colon(painter, x, y, ref_w, ref_h, on_color, off_color, is_on=True):
    """绘制由两个小方块组成的冒号。ref_w/ref_h 仅用于比例参考。"""
    painter.setPen(Qt.PenStyle.NoPen)
    color_on = QColor(on_color) if is_on else QColor(off_color)
    # 方块尺寸基于参考尺寸，保持与数字笔画协调
    block_size = min(ref_w, ref_h) * 0.18
    # 依据原布局推导出的中心距：0.36 * ref_h
    gap = max(block_size * 0.2, ref_h * 0.36 - block_size)  # 防止负值
    top_y = y
    bottom_y = y + block_size + gap
    painter.setBrush(color_on)
    painter.drawRect(int(x), int(top_y), int(block_size), int(block_size))
    painter.drawRect(int(x), int(bottom_y), int(block_size), int(block_size))


def export_colon(output_dir="digits", digit_w=120, digit_h=200, main_color="#C70039"):
    """绘制冒号的点亮/熄灭状态，保存两张PNG。图片尺寸紧贴冒号本身。"""
    os.makedirs(output_dir, exist_ok=True)
    off_color = QColor(100, 100, 100, 80)

    # 计算尺寸：紧贴两方块的包围盒
    block_size = min(digit_w, digit_h) * 0.18
    gap = max(block_size * 0.2, digit_h * 0.36 - block_size)
    img_w = int(block_size)
    img_h = int(block_size * 2 + gap)

    for state, name in [(True, "colon_on"), (False, "colon_off")]:
        img = QImage(img_w, img_h, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # ******** 修改3：冒号点亮色同步改为深红色 ********
        draw_colon(painter, 0, 0, digit_w, digit_h, main_color, off_color, is_on=state)
        painter.end()
        img.save(os.path.join(output_dir, f"{name}.png"))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 直接导出 0-9 数字到 digits 目录
    export_digits(output_dir="digits", digit_w=120, digit_h=200, main_color='#000000', highlight_color='#666666')
    export_colon(output_dir="digits", digit_w=120, digit_h=200, main_color='#000000')
    sys.exit(0)