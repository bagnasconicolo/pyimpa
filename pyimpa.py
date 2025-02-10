#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json  # for saving/loading presets
import numpy as np
from PIL import Image

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QSpinBox, QMessageBox,
    QLineEdit, QGroupBox, QCheckBox, QComboBox, QGridLayout, QDialog,
    QFormLayout, QDialogButtonBox, QListWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QIcon

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------------------
# ------------------------------ EXISTING CODE, UNCHANGED --------------------------------
# ---------------------------------------------------------------------------------------

# Color & style maps
LINE_COLOR_MAP = {
    "Black": "black",
    "Red": "red",
    "Blue": "blue",
    "Green": "green",
    "Magenta": "magenta",
    "Cyan": "cyan",
    "Orange": "orange",
    "Gray": "gray"
}
LINE_STYLE_MAP = {
    "Solid": "-",
    "Dashed": "--",
    "Dotted": ":",
    "Dash-Dot": "-."
}
MARKER_MAP = {
    "None": "",
    "Circle (o)": "o",
    "Square (s)": "s",
    "Triangle (^)": "^",
    "Diamond (D)": "D",
    "Plus (+)": "+",
    "Cross (x)": "x",
    "Star (*)": "*"
}

def extract_channel(rgb_array, channel_mode):
    """
    If array is shape (H, W, 3), pick R/G/B or Gray.
    If array is shape (H, W), assume grayscale => return as is.
    """
    if rgb_array.ndim == 2:
        return rgb_array
    else:
        if channel_mode == "Gray":
            return np.mean(rgb_array, axis=2).astype(np.uint8)
        elif channel_mode == "Red":
            return rgb_array[..., 0]
        elif channel_mode == "Green":
            return rgb_array[..., 1]
        elif channel_mode == "Blue":
            return rgb_array[..., 2]
        else:
            return np.mean(rgb_array, axis=2).astype(np.uint8)

# ---------------------------------------------------------------------------------------
# ------------------------------ IMAGE LABEL CLASS ---------------------------------------
# ---------------------------------------------------------------------------------------

class ImageLabel(QLabel):
    """
    Displays the main image and allows the user to draw/drag two points.
    The image is displayed at its native resolution (1:1 mapping).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Do not scale contents so that the native resolution is preserved.
        self.setScaledContents(False)
        self.setMinimumSize(300, 200)

        self.image_array = None     # (H, W) or (H, W, 3)
        self.pixmap_orig = None
        self.pixmap_displayed = None

        # Points & dragging
        self.point1 = None
        self.point2 = None
        self.dragging_point = None
        self.drag_threshold = 10
        self.handle_size = 6

        # Bandwidth for band extraction
        self.bandwidth = 0

        # Drawing mode flag
        self.drawing_enabled = False

    def load_image(self, file_path):
        if not file_path:
            return
        # Load image as RGB so that we can extract channels
        pil_image = Image.open(file_path).convert('RGB')
        self.image_array = np.array(pil_image)  # shape (H, W, 3)
        mw = self.window()
        if hasattr(mw, "channel_combo"):
            channel_mode = mw.channel_combo.currentText()
        else:
            channel_mode = "Gray"
        display_array = extract_channel(self.image_array, channel_mode)
        qimg = self._to_qimage(display_array)
        self.pixmap_orig = QPixmap.fromImage(qimg)
        self.update_displayed_pixmap()
        # Reset points
        self.point1 = None
        self.point2 = None
        self.dragging_point = None

    def set_bandwidth(self, bw):
        self.bandwidth = bw
        self.update_segment_display()

    def enable_drawing(self, enable):
        self.drawing_enabled = enable

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # In precise mode, we do not scale the image; simply update overlays.
        self.update_segment_display()

    def update_displayed_pixmap(self):
        if self.pixmap_orig is None:
            return
        # Do not scale the image; keep native resolution.
        self.pixmap_displayed = self.pixmap_orig
        self.setPixmap(self.pixmap_displayed)
        # Adjust the widget size to the pixmap size so nothing is cropped.
        self.adjustSize()
        self.update_segment_display()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos_label = event.pos()
            if self.drawing_enabled:
                if self.point1 is None:
                    self.point1 = self._label_coords_to_image_coords(pos_label)
                    self.window().update_point_info(first_point=self.point1, second_point=None)
                elif self.point2 is None:
                    self.point2 = self._label_coords_to_image_coords(pos_label)
                    self.window().update_point_info(first_point=self.point1, second_point=self.point2)
                    self.drawing_enabled = False
                self.update_segment_display()
            else:
                if self.point1 and self.point2:
                    p1_screen = self._image_coords_to_label_coords(self.point1)
                    p2_screen = self._image_coords_to_label_coords(self.point2)
                    dist_p1 = np.hypot(p1_screen[0] - pos_label.x(), p1_screen[1] - pos_label.y())
                    dist_p2 = np.hypot(p2_screen[0] - pos_label.x(), p2_screen[1] - pos_label.y())
                    if dist_p1 < self.drag_threshold:
                        self.dragging_point = "p1"
                    elif dist_p2 < self.drag_threshold:
                        self.dragging_point = "p2"
                    else:
                        self.dragging_point = None

    def mouseMoveEvent(self, event):
        if self.dragging_point is not None:
            pos_label = event.pos()
            new_img_coords = self._label_coords_to_image_coords(pos_label)
            if self.dragging_point == "p1":
                self.point1 = new_img_coords
            elif self.dragging_point == "p2":
                self.point2 = new_img_coords
            self.window().update_point_info(first_point=self.point1, second_point=self.point2)
            self.update_segment_display()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_point = None

    def update_segment_display(self):
        if self.pixmap_displayed is None:
            return
        # Make a copy of the native-resolution pixmap to overlay points/lines.
        pixmap_copy = self.pixmap_displayed.copy()
        painter = QPainter(pixmap_copy)
        if self.point1 is not None:
            self._draw_handle(painter, self.point1, color=Qt.red)
        if self.point2 is not None:
            self._draw_handle(painter, self.point2, color=Qt.red)
        if self.point1 is not None and self.point2 is not None:
            self._draw_line_on_pixmap(painter, self.point1, self.point2,
                                      color=Qt.red, pen_width=3, pen_style=Qt.SolidLine)
            if self.bandwidth > 0:
                dx = self.point2[0] - self.point1[0]
                dy = self.point2[1] - self.point1[1]
                length = np.hypot(dx, dy)
                if length != 0:
                    perp_x = dy / length
                    perp_y = -dx / length
                    half_band = self.bandwidth // 2
                    p1_plus = (self.point1[0] + half_band * perp_x, self.point1[1] + half_band * perp_y)
                    p2_plus = (self.point2[0] + half_band * perp_x, self.point2[1] + half_band * perp_y)
                    p1_minus = (self.point1[0] - half_band * perp_x, self.point1[1] - half_band * perp_y)
                    p2_minus = (self.point2[0] - half_band * perp_x, self.point2[1] - half_band * perp_y)
                    self._draw_line_on_pixmap(painter, p1_plus, p2_plus,
                                              color=Qt.green, pen_width=2, pen_style=Qt.SolidLine)
                    self._draw_line_on_pixmap(painter, p1_minus, p2_minus,
                                              color=Qt.green, pen_width=2, pen_style=Qt.SolidLine)
        painter.end()
        self.setPixmap(pixmap_copy)
        self.window().update_magnifiers()
        self.window().update_band_preview()

    def _draw_handle(self, painter, point, color=Qt.red):
        center_screen = self._image_coords_to_label_coords(point)
        pen = QPen(color, 2, Qt.SolidLine)
        painter.setPen(pen)
        painter.setBrush(color)
        r = self.handle_size
        painter.drawEllipse(QRect(center_screen[0] - r, center_screen[1] - r, 2*r, 2*r))

    def _draw_line_on_pixmap(self, painter, p1, p2, color=Qt.red, pen_width=2, pen_style=Qt.SolidLine):
        pen = QPen(color, pen_width, pen_style)
        painter.setPen(pen)
        x1, y1 = self._image_coords_to_label_coords(p1)
        x2, y2 = self._image_coords_to_label_coords(p2)
        painter.drawLine(x1, y1, x2, y2)

    def _label_coords_to_image_coords(self, pos):
        if self.pixmap_displayed is None or self.image_array is None:
            return (0, 0)
        disp_w = self.pixmap_displayed.width()
        disp_h = self.pixmap_displayed.height()
        if self.image_array.ndim == 3:
            orig_h, orig_w, _ = self.image_array.shape
        else:
            orig_h, orig_w = self.image_array.shape
        if disp_w == 0 or disp_h == 0:
            return (0, 0)
        scale_x = orig_w / disp_w
        scale_y = orig_h / disp_h
        x_img = int(pos.x() * scale_x)
        y_img = int(pos.y() * scale_y)
        x_img = max(0, min(orig_w - 1, x_img))
        y_img = max(0, min(orig_h - 1, y_img))
        return (x_img, y_img)

    def _image_coords_to_label_coords(self, p):
        if self.pixmap_displayed is None or self.image_array is None:
            return (0, 0)
        orig_x, orig_y = p
        if self.image_array.ndim == 3:
            orig_h, orig_w, _ = self.image_array.shape
        else:
            orig_h, orig_w = self.image_array.shape
        disp_w = self.pixmap_displayed.width()
        disp_h = self.pixmap_displayed.height()
        if orig_w == 0 or orig_h == 0:
            return (0, 0)
        scale_x = disp_w / orig_w
        scale_y = disp_h / orig_h
        x_label = int(orig_x * scale_x)
        y_label = int(orig_y * scale_y)
        return (x_label, y_label)

    def _to_qimage(self, gray_array):
        h, w = gray_array.shape
        bytes_per_line = w
        return QImage(
            gray_array.astype(np.uint8, copy=False).tobytes(),
            w,
            h,
            bytes_per_line,
            QImage.Format_Grayscale8
        )

# ---------------------------------------------------------------------------------------
# ------------------------------- BAND PREVIEW LABEL -------------------------------------
# ---------------------------------------------------------------------------------------

class BandPreviewLabel(QLabel):
    """
    Shows the rectified band in a small preview.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(True)
        self.setMaximumSize(400, 400)

    def update_band_image(self, band_array):
        if band_array is None or band_array.size == 0:
            self.clear()
            return
        band_array = band_array.astype(np.uint8, copy=False)
        h, w = band_array.shape
        bytes_per_line = w
        qimg = QImage(
            band_array.tobytes(),
            w,
            h,
            bytes_per_line,
            QImage.Format_Grayscale8
        )
        pix = QPixmap.fromImage(qimg)
        self.setPixmap(pix)

# ---------------------------------------------------------------------------------------
# ----------------------------- MAGNIFIER LABEL CLASS ------------------------------------
# ---------------------------------------------------------------------------------------

class MagnifierLabel(QLabel):
    """
    A small "magnifier" that shows a zoomed area around a point.
    """
    def __init__(self, size=120, parent=None):
        super().__init__(parent)
        self.magnifier_size = size
        self.setFixedSize(size, size)
        self.setScaledContents(True)
        self.setStyleSheet("background-color: #333;")

    def update_magnifier(self, image_array, point, zoom=4):
        if image_array is None or point is None:
            self.clear()
            return
        mw = self.window()
        if hasattr(mw, "channel_combo"):
            channel_mode = mw.channel_combo.currentText()
        else:
            channel_mode = "Gray"
        if image_array.ndim == 3:
            array_2d = extract_channel(image_array, channel_mode)
        else:
            array_2d = image_array
        px, py = point
        h, w = array_2d.shape
        half_w = self.magnifier_size // (2 * zoom)
        if half_w < 1:
            half_w = 1
        x1 = max(0, px - half_w)
        x2 = min(w, px + half_w)
        y1 = max(0, py - half_w)
        y2 = min(h, py + half_w)
        cropped = array_2d[y1:y2, x1:x2]
        if cropped.size == 0:
            self.clear()
            return
        qimg = QImage(
            cropped.astype(np.uint8, copy=False).tobytes(),
            cropped.shape[1],
            cropped.shape[0],
            cropped.shape[1],
            QImage.Format_Grayscale8
        )
        pix = QPixmap.fromImage(qimg)
        pix_zoomed = pix.scaled(self.magnifier_size * zoom, self.magnifier_size * zoom,
                                Qt.KeepAspectRatio, Qt.FastTransformation)
        cross_copy = pix_zoomed.copy()
        painter = QPainter(cross_copy)
        painter.setRenderHint(QPainter.Antialiasing, False)
        cross_color = Qt.red
        pen = QPen(cross_color, 2, Qt.SolidLine)
        painter.setPen(pen)
        cx = cross_copy.width() // 2
        cy = cross_copy.height() // 2
        painter.drawLine(cx, 0, cx, cross_copy.height())
        painter.drawLine(0, cy, cross_copy.width(), cy)
        r_dot = 6
        painter.setBrush(cross_color)
        painter.drawEllipse(cx - r_dot//2, cy - r_dot//2, r_dot, r_dot)
        painter.end()
        final_pix = cross_copy.scaled(self.magnifier_size,
                                      self.magnifier_size,
                                      Qt.KeepAspectRatio,
                                      Qt.FastTransformation)
        self.setPixmap(final_pix)

# ---------------------------------------------------------------------------------------
# ------------------------------ NEW/EXISTING UTILITY CLASSES ----------------------------
# ---------------------------------------------------------------------------------------

class SeparateWindow(QMainWindow):
    """
    A separate window to display the image, magnifiers, and band preview.
    """
    def __init__(self, parent=None, image_label=None, band_label=None, mag1=None, mag2=None):
        super().__init__(parent)
        self.setWindowTitle("Separate Image Window (Vertical Layout)")
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        main_vlayout = QVBoxLayout()
        self.main_widget.setLayout(main_vlayout)
        if image_label is not None and image_label.pixmap_displayed is not None:
            lbl_img = QLabel()
            lbl_img.setPixmap(image_label.pixmap_displayed)
            lbl_img.setScaledContents(True)
            main_vlayout.addWidget(lbl_img)
        if mag1 is not None and mag1.pixmap():
            lbl_mag1 = QLabel()
            lbl_mag1.setPixmap(mag1.pixmap())
            lbl_mag1.setScaledContents(True)
            main_vlayout.addWidget(lbl_mag1)
        if mag2 is not None and mag2.pixmap():
            lbl_mag2 = QLabel()
            lbl_mag2.setPixmap(mag2.pixmap())
            lbl_mag2.setScaledContents(True)
            main_vlayout.addWidget(lbl_mag2)
        if band_label is not None and band_label.pixmap():
            lbl_band = QLabel()
            lbl_band.setPixmap(band_label.pixmap())
            lbl_band.setScaledContents(True)
            main_vlayout.addWidget(lbl_band)

class SavePresetDialog(QDialog):
    """
    A simple dialog to choose which settings to save.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Preset Options")
        self.selected_options = {
            "Channel": False,
            "Bandwidth": False,
            "BinSize": False,
            "ShowMinMax": False,
            "ShowErrorbar": False,
            "PlotStyling": False
        }
        self.preset_name = ""
        form_layout = QFormLayout()
        self.name_edit = QLineEdit("")
        form_layout.addRow("Preset Name:", self.name_edit)
        self.chk_channel = QCheckBox("Channel")
        self.chk_bandwidth = QCheckBox("Bandwidth")
        self.chk_binsize = QCheckBox("Bin size")
        self.chk_minmax = QCheckBox("Show Min/Max")
        self.chk_errorbar = QCheckBox("Show Error Bar")
        self.chk_style   = QCheckBox("Plot Styling (colors, lines, etc.)")
        form_layout.addRow(self.chk_channel)
        form_layout.addRow(self.chk_bandwidth)
        form_layout.addRow(self.chk_binsize)
        form_layout.addRow(self.chk_minmax)
        form_layout.addRow(self.chk_errorbar)
        form_layout.addRow(self.chk_style)
        self.existing_list = QListWidget()
        preset_dir = os.getcwd()
        for f in os.listdir(preset_dir):
            if f.lower().endswith(".json"):
                self.existing_list.addItem(f)
        form_layout.addRow(QLabel("Existing Presets in folder:"))
        form_layout.addRow(self.existing_list)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        form_layout.addWidget(button_box)
        self.setLayout(form_layout)

    def accept(self):
        self.selected_options["Channel"] = self.chk_channel.isChecked()
        self.selected_options["Bandwidth"] = self.chk_bandwidth.isChecked()
        self.selected_options["BinSize"] = self.chk_binsize.isChecked()
        self.selected_options["ShowMinMax"] = self.chk_minmax.isChecked()
        self.selected_options["ShowErrorbar"] = self.chk_errorbar.isChecked()
        self.selected_options["PlotStyling"] = self.chk_style.isChecked()
        self.preset_name = self.name_edit.text().strip()
        super().accept()

# ---------------------------------------------------------------------------------------
# ------------------------------ MAINWINDOW CLASS ----------------------------------------
# ---------------------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        icon_path = os.path.join(os.path.dirname(__file__), "pyim.png")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print("[WARN] Icon not found, proceeding without icon.")

        self.setWindowTitle("Multi-Channel Intensity Profile (RGB or Gray)")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout: left panel for display, right panel for controls.
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # ------------------- Left Panel: Image Display, Magnifiers, Band Preview -------------------
        left_layout = QVBoxLayout()

        # Use a scroll area for the image display so the full (native) image can be viewed.
        img_group = QGroupBox("Loaded Image")
        img_layout = QVBoxLayout()
        self.image_label = ImageLabel()  # displays image at native resolution
        scroll = QScrollArea()
        scroll.setWidget(self.image_label)
        scroll.setWidgetResizable(False)
        img_layout.addWidget(scroll)
        img_group.setLayout(img_layout)
        left_layout.addWidget(img_group)

        # Magnifiers
        mag_group = QGroupBox("Magnifiers")
        mag_layout = QHBoxLayout()
        self.mag1_label = MagnifierLabel(size=120)
        self.mag2_label = MagnifierLabel(size=120)
        mag_layout.addWidget(self.mag1_label)
        mag_layout.addWidget(self.mag2_label)
        mag_group.setLayout(mag_layout)
        left_layout.addWidget(mag_group)

        # Band preview
        band_group = QGroupBox("Band Preview")
        band_layout = QVBoxLayout()
        self.band_preview_label = BandPreviewLabel()
        band_layout.addWidget(self.band_preview_label)
        band_group.setLayout(band_layout)
        left_layout.addWidget(band_group)

        # ------------------- Right Panel: Controls -------------------
        right_layout = QVBoxLayout()

        # Profile Parameters
        param_box = QGroupBox("Profile Parameters")
        param_layout = QHBoxLayout()
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        param_layout.addWidget(self.load_button)
        self.draw_button = QPushButton("Draw Segment")
        self.draw_button.clicked.connect(self.activate_drawing)
        param_layout.addWidget(self.draw_button)
        param_layout.addWidget(QLabel("Bandwidth (px):"))
        self.bandwidth_spin = QSpinBox()
        self.bandwidth_spin.setRange(0, 200)
        self.bandwidth_spin.setValue(2)
        self.bandwidth_spin.valueChanged.connect(self.update_bandwidth)
        param_layout.addWidget(self.bandwidth_spin)
        self.profile_button = QPushButton("Calculate Profile")
        self.profile_button.clicked.connect(self.calculate_profile)
        param_layout.addWidget(self.profile_button)
        param_box.setLayout(param_layout)
        right_layout.addWidget(param_box)

        # Channel Selection
        channel_box = QGroupBox("Channel Selection")
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channel:"))
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Gray", "Red", "Green", "Blue"])
        self.channel_combo.setCurrentText("Gray")
        self.channel_combo.currentIndexChanged.connect(self.on_channel_changed)
        channel_layout.addWidget(self.channel_combo)
        channel_box.setLayout(channel_layout)
        right_layout.addWidget(channel_box)

        # Manual Coordinate Edits
        manual_coord_box = QGroupBox("Manual Coordinate Edits")
        manual_coord_layout = QHBoxLayout()
        manual_coord_layout.addWidget(QLabel("X1:"))
        self.x1_edit = QSpinBox()
        self.x1_edit.setRange(0, 999999)
        manual_coord_layout.addWidget(self.x1_edit)
        manual_coord_layout.addWidget(QLabel("Y1:"))
        self.y1_edit = QSpinBox()
        self.y1_edit.setRange(0, 999999)
        manual_coord_layout.addWidget(self.y1_edit)
        manual_coord_layout.addWidget(QLabel("X2:"))
        self.x2_edit = QSpinBox()
        self.x2_edit.setRange(0, 999999)
        manual_coord_layout.addWidget(self.x2_edit)
        manual_coord_layout.addWidget(QLabel("Y2:"))
        self.y2_edit = QSpinBox()
        self.y2_edit.setRange(0, 999999)
        manual_coord_layout.addWidget(self.y2_edit)
        apply_coords_btn = QPushButton("Apply Manual Coordinates")
        apply_coords_btn.clicked.connect(self.apply_manual_coords)
        manual_coord_layout.addWidget(apply_coords_btn)
        manual_coord_box.setLayout(manual_coord_layout)
        right_layout.addWidget(manual_coord_box)

        # Visualization Window Button
        self.separate_win_button = QPushButton("Open Visualization Window")
        self.separate_win_button.clicked.connect(self.open_in_separate_window)
        right_layout.addWidget(self.separate_win_button)

        # Preset Saving/Loading
        preset_layout = QHBoxLayout()
        self.save_preset_button = QPushButton("Save Preset")
        self.save_preset_button.clicked.connect(self.save_preset)
        preset_layout.addWidget(self.save_preset_button)
        self.load_preset_button = QPushButton("Load Preset")
        self.load_preset_button.clicked.connect(self.load_preset)
        preset_layout.addWidget(self.load_preset_button)
        right_layout.addLayout(preset_layout)

        # Chart & Binning Options
        chart_box = QGroupBox("Chart & Binning Options")
        chart_layout = QGridLayout()
        fixed_width = 160
        label_title = QLabel("Graph Title:")
        self.title_edit = QLineEdit("Binning & Error Bars")
        self.title_edit.setFixedWidth(fixed_width)
        label_xlabel = QLabel("X Axis Label:")
        self.xlabel_edit = QLineEdit("Pos segm")
        self.xlabel_edit.setFixedWidth(fixed_width)
        label_ylabel = QLabel("Y Axis Label:")
        self.ylabel_edit = QLineEdit("Intensity")
        self.ylabel_edit.setFixedWidth(fixed_width)
        chart_layout.addWidget(label_title,   0, 0)
        chart_layout.addWidget(self.title_edit, 0, 1)
        chart_layout.addWidget(label_xlabel,  1, 0)
        chart_layout.addWidget(self.xlabel_edit, 1, 1)
        chart_layout.addWidget(label_ylabel,  2, 0)
        chart_layout.addWidget(self.ylabel_edit, 2, 1)
        label_band_title = QLabel("Band Title:")
        self.band_title_edit = QLineEdit("Rectified Band")
        self.band_title_edit.setFixedWidth(fixed_width)
        label_band_xlabel = QLabel("Band X Label:")
        self.band_xlabel_edit = QLineEdit("Pos seg")
        self.band_xlabel_edit.setFixedWidth(fixed_width)
        label_band_ylabel = QLabel("Band Y Label:")
        self.band_ylabel_edit = QLineEdit("Offset")
        self.band_ylabel_edit.setFixedWidth(fixed_width)
        chart_layout.addWidget(label_band_title,   0, 2)
        chart_layout.addWidget(self.band_title_edit, 0, 3)
        chart_layout.addWidget(label_band_xlabel,  1, 2)
        chart_layout.addWidget(self.band_xlabel_edit, 1, 3)
        chart_layout.addWidget(label_band_ylabel,  2, 2)
        chart_layout.addWidget(self.band_ylabel_edit, 2, 3)
        label_bin = QLabel("Bin size (# avg per bin):")
        self.bin_spin = QSpinBox()
        self.bin_spin.setRange(1, 1000)
        self.bin_spin.setValue(10)
        bin_hint = QLabel("(# avg per bin)")
        bin_hint.setStyleSheet("font-size: 9px; color: gray;")
        chart_layout.addWidget(label_bin,   3, 0)
        chart_layout.addWidget(self.bin_spin, 3, 1)
        self.show_minmax_checkbox = QCheckBox("Show Min/Max")
        self.show_minmax_checkbox.setChecked(True)
        self.show_errorbar_checkbox = QCheckBox("Error Bar")
        self.show_errorbar_checkbox.setChecked(True)
        self.show_centerline_checkbox = QCheckBox("Center line")
        self.show_centerline_checkbox.setChecked(False)
        self.show_profile_grid_checkbox = QCheckBox("Grid Prof.")
        self.show_profile_grid_checkbox.setChecked(True)
        self.show_band_grid_checkbox = QCheckBox("Grid Band")
        self.show_band_grid_checkbox.setChecked(True)
        chart_layout.addWidget(self.show_minmax_checkbox,     0, 6)
        chart_layout.addWidget(self.show_errorbar_checkbox,   1, 6)
        chart_layout.addWidget(self.show_centerline_checkbox, 2, 6)
        chart_layout.addWidget(self.show_profile_grid_checkbox, 3, 6)
        chart_layout.addWidget(self.show_band_grid_checkbox,    4, 6)
        label_center_color = QLabel("Center color:")
        self.center_color_combo = QComboBox()
        for color_name in LINE_COLOR_MAP.keys():
            self.center_color_combo.addItem(color_name)
        self.center_color_combo.setCurrentText("Black")
        label_center_style = QLabel("Center style:")
        self.center_style_combo = QComboBox()
        for style_name in LINE_STYLE_MAP.keys():
            self.center_style_combo.addItem(style_name)
        self.center_style_combo.setCurrentText("Solid")
        label_center_thick = QLabel("Center thick:")
        self.center_thick_spin = QSpinBox()
        self.center_thick_spin.setRange(1, 10)
        self.center_thick_spin.setValue(2)
        chart_layout.addWidget(label_center_color, 0, 7)
        chart_layout.addWidget(self.center_color_combo, 0, 8)
        chart_layout.addWidget(label_center_style, 1, 7)
        chart_layout.addWidget(self.center_style_combo, 1, 8)
        chart_layout.addWidget(label_center_thick, 2, 7)
        chart_layout.addWidget(self.center_thick_spin, 2, 8)
        label_min_color = QLabel("Min color:")
        self.min_line_color_combo = QComboBox()
        for cn in LINE_COLOR_MAP.keys():
            self.min_line_color_combo.addItem(cn)
        self.min_line_color_combo.setCurrentText("Red")
        label_min_style = QLabel("Min style:")
        self.min_line_style_combo = QComboBox()
        for st in LINE_STYLE_MAP.keys():
            self.min_line_style_combo.addItem(st)
        self.min_line_style_combo.setCurrentText("Solid")
        label_min_thick = QLabel("Min thick:")
        self.min_line_thick_spin = QSpinBox()
        self.min_line_thick_spin.setRange(1, 10)
        self.min_line_thick_spin.setValue(2)
        chart_layout.addWidget(label_min_color, 3, 7)
        chart_layout.addWidget(self.min_line_color_combo, 3, 8)
        chart_layout.addWidget(label_min_style, 4, 7)
        chart_layout.addWidget(self.min_line_style_combo, 4, 8)
        chart_layout.addWidget(label_min_thick, 5, 7)
        chart_layout.addWidget(self.min_line_thick_spin, 5, 8)
        label_max_color = QLabel("Max color:")
        self.max_line_color_combo = QComboBox()
        for cn in LINE_COLOR_MAP.keys():
            self.max_line_color_combo.addItem(cn)
        self.max_line_color_combo.setCurrentText("Blue")
        label_max_style = QLabel("Max style:")
        self.max_line_style_combo = QComboBox()
        for st in LINE_STYLE_MAP.keys():
            self.max_line_style_combo.addItem(st)
        self.max_line_style_combo.setCurrentText("Solid")
        label_max_thick = QLabel("Max thick:")
        self.max_line_thick_spin = QSpinBox()
        self.max_line_thick_spin.setRange(1, 10)
        self.max_line_thick_spin.setValue(2)
        chart_layout.addWidget(label_max_color, 6, 7)
        chart_layout.addWidget(self.max_line_color_combo, 6, 8)
        chart_layout.addWidget(label_max_style, 7, 7)
        chart_layout.addWidget(self.max_line_style_combo, 7, 8)
        chart_layout.addWidget(label_max_thick, 8, 7)
        chart_layout.addWidget(self.max_line_thick_spin, 8, 8)
        label_mean_color = QLabel("Mean color:")
        self.mean_line_color_combo = QComboBox()
        for cn in LINE_COLOR_MAP.keys():
            self.mean_line_color_combo.addItem(cn)
        self.mean_line_color_combo.setCurrentText("Black")
        label_mean_style = QLabel("Mean style:")
        self.mean_line_style_combo = QComboBox()
        for st in LINE_STYLE_MAP.keys():
            self.mean_line_style_combo.addItem(st)
        self.mean_line_style_combo.setCurrentText("Solid")
        label_mean_thick = QLabel("Mean thick:")
        self.mean_line_thick_spin = QSpinBox()
        self.mean_line_thick_spin.setRange(0, 10)  # 0 => no line
        self.mean_line_thick_spin.setValue(2)
        label_marker = QLabel("Mean marker:")
        self.mean_marker_combo = QComboBox()
        for mk in MARKER_MAP.keys():
            self.mean_marker_combo.addItem(mk)
        self.mean_marker_combo.setCurrentText("None")
        label_marker_size = QLabel("Marker size:")
        self.mean_marker_size_spin = QSpinBox()
        self.mean_marker_size_spin.setRange(1, 20)
        self.mean_marker_size_spin.setValue(6)
        row_start = 5
        chart_layout.addWidget(label_mean_color,      row_start,   0)
        chart_layout.addWidget(self.mean_line_color_combo, row_start, 1)
        chart_layout.addWidget(label_mean_style,      row_start+1, 0)
        chart_layout.addWidget(self.mean_line_style_combo, row_start+1, 1)
        chart_layout.addWidget(label_mean_thick,      row_start+2, 0)
        chart_layout.addWidget(self.mean_line_thick_spin,  row_start+2, 1)
        chart_layout.addWidget(label_marker,          row_start,   2)
        chart_layout.addWidget(self.mean_marker_combo, row_start,   3)
        chart_layout.addWidget(label_marker_size,     row_start+1, 2)
        chart_layout.addWidget(self.mean_marker_size_spin, row_start+1, 3)
        chart_box.setLayout(chart_layout)
        right_layout.addWidget(chart_box)

        self.coord_label = QLabel("First point: (---, ---), Second point: (---, ---)")
        right_layout.addWidget(self.coord_label)
        right_layout.addStretch()

        # Add the two panels to the main layout
        main_layout.addLayout(left_layout, stretch=2)
        main_layout.addLayout(right_layout, stretch=1)

        self.resize(1400, 700)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        if file_path:
            self.image_label.load_image(file_path)

    def activate_drawing(self):
        if self.image_label.image_array is None:
            QMessageBox.warning(self, "Warning", "Please load an image first!")
            return
        self.image_label.set_bandwidth(self.bandwidth_spin.value())
        self.image_label.point1 = None
        self.image_label.point2 = None
        self.image_label.enable_drawing(True)

    def update_bandwidth(self):
        bw = self.bandwidth_spin.value()
        self.image_label.set_bandwidth(bw)

    def on_channel_changed(self):
        if self.image_label.image_array is None:
            return
        channel_mode = self.channel_combo.currentText()
        if self.image_label.image_array.ndim == 2:
            array_2d = self.image_label.image_array
        else:
            array_2d = extract_channel(self.image_label.image_array, channel_mode)
        qimg = self.image_label._to_qimage(array_2d)
        self.image_label.pixmap_orig = QPixmap.fromImage(qimg)
        self.image_label.update_displayed_pixmap()

    def update_point_info(self, first_point=None, second_point=None):
        if first_point is not None and second_point is None:
            (x1, y1) = first_point
            self.coord_label.setText(
                f"First point: ({x1}, {y1}), Second point: (---, ---)"
            )
            self.x1_edit.setValue(x1)
            self.y1_edit.setValue(y1)
        elif first_point is not None and second_point is not None:
            (x1, y1) = first_point
            (x2, y2) = second_point
            length = int(np.hypot(x2 - x1, y2 - y1))
            self.coord_label.setText(
                f"First point: ({x1}, {y1}), Second point: ({x2}, {y2}) - Dist={length}"
            )
            self.x1_edit.setValue(x1)
            self.y1_edit.setValue(y1)
            self.x2_edit.setValue(x2)
            self.y2_edit.setValue(y2)

    def apply_manual_coords(self):
        x1 = self.x1_edit.value()
        y1 = self.y1_edit.value()
        x2 = self.x2_edit.value()
        y2 = self.y2_edit.value()
        self.image_label.point1 = (x1, y1)
        self.image_label.point2 = (x2, y2)
        self.update_point_info(self.image_label.point1, self.image_label.point2)
        self.image_label.update_segment_display()

    def open_in_separate_window(self):
        if self.image_label.pixmap_displayed is None:
            QMessageBox.warning(self, "Warning", "No image loaded or segment not drawn.")
            return
        sep_win = SeparateWindow(
            parent=self,
            image_label=self.image_label,
            band_label=self.band_preview_label,
            mag1=self.mag1_label,
            mag2=self.mag2_label
        )
        sep_win.show()
        self.separate_win = sep_win

    def save_preset(self):
        if self.image_label.image_array is None:
            QMessageBox.warning(self, "Warning", "No image loaded yet.")
            return
        dlg = SavePresetDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            sel = dlg.selected_options
            preset_name = dlg.preset_name
            if not preset_name:
                preset_name = "unnamed_preset"
            data_to_save = {}
            if sel["Channel"]:
                data_to_save["channel"] = self.channel_combo.currentText()
            if sel["Bandwidth"]:
                data_to_save["bandwidth"] = self.bandwidth_spin.value()
            if sel["BinSize"]:
                data_to_save["bin"] = self.bin_spin.value()
            if sel["ShowMinMax"]:
                data_to_save["show_minmax"] = self.show_minmax_checkbox.isChecked()
            if sel["ShowErrorbar"]:
                data_to_save["show_error"] = self.show_errorbar_checkbox.isChecked()
            if sel["PlotStyling"]:
                data_to_save["mean_line_color"] = self.mean_line_color_combo.currentText()
                data_to_save["mean_line_style"] = self.mean_line_style_combo.currentText()
                data_to_save["mean_line_thick"] = self.mean_line_thick_spin.value()
                data_to_save["mean_marker"]     = self.mean_marker_combo.currentText()
                data_to_save["mean_marker_size"]= self.mean_marker_size_spin.value()
                data_to_save["min_line_color"]  = self.min_line_color_combo.currentText()
                data_to_save["min_line_style"]  = self.min_line_style_combo.currentText()
                data_to_save["min_line_thick"]  = self.min_line_thick_spin.value()
                data_to_save["max_line_color"]  = self.max_line_color_combo.currentText()
                data_to_save["max_line_style"]  = self.max_line_style_combo.currentText()
                data_to_save["max_line_thick"]  = self.max_line_thick_spin.value()
                data_to_save["center_color"]    = self.center_color_combo.currentText()
                data_to_save["center_style"]    = self.center_style_combo.currentText()
                data_to_save["center_thick"]    = self.center_thick_spin.value()
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Preset JSON", preset_name+".json", "JSON (*.json)")
            if file_path:
                with open(file_path, "w") as f:
                    json.dump(data_to_save, f, indent=2)
                QMessageBox.information(self, "Info", f"Preset saved to {file_path}")

    def load_preset(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Preset JSON", "", "JSON (*.json)")
        if file_path:
            with open(file_path, "r") as f:
                data = json.load(f)
            if "channel" in data:
                c = data["channel"]
                if c in ["Gray", "Red", "Green", "Blue"]:
                    self.channel_combo.setCurrentText(c)
            if "bandwidth" in data:
                self.bandwidth_spin.setValue(data["bandwidth"])
            if "bin" in data:
                self.bin_spin.setValue(data["bin"])
            if "show_minmax" in data:
                self.show_minmax_checkbox.setChecked(data["show_minmax"])
            if "show_error" in data:
                self.show_errorbar_checkbox.setChecked(data["show_error"])
            if "mean_line_color" in data:
                self.mean_line_color_combo.setCurrentText(data["mean_line_color"])
            if "mean_line_style" in data:
                self.mean_line_style_combo.setCurrentText(data["mean_line_style"])
            if "mean_line_thick" in data:
                self.mean_line_thick_spin.setValue(data["mean_line_thick"])
            if "mean_marker" in data:
                self.mean_marker_combo.setCurrentText(data["mean_marker"])
            if "mean_marker_size" in data:
                self.mean_marker_size_spin.setValue(data["mean_marker_size"])
            if "min_line_color" in data:
                self.min_line_color_combo.setCurrentText(data["min_line_color"])
            if "min_line_style" in data:
                self.min_line_style_combo.setCurrentText(data["min_line_style"])
            if "min_line_thick" in data:
                self.min_line_thick_spin.setValue(data["min_line_thick"])
            if "max_line_color" in data:
                self.max_line_color_combo.setCurrentText(data["max_line_color"])
            if "max_line_style" in data:
                self.max_line_style_combo.setCurrentText(data["max_line_style"])
            if "max_line_thick" in data:
                self.max_line_thick_spin.setValue(data["max_line_thick"])
            if "center_color" in data:
                self.center_color_combo.setCurrentText(data["center_color"])
            if "center_style" in data:
                self.center_style_combo.setCurrentText(data["center_style"])
            if "center_thick" in data:
                self.center_thick_spin.setValue(data["center_thick"])
            QMessageBox.information(self, "Info", f"Preset loaded from {file_path}")

    def update_band_preview(self):
        if (self.image_label.point1 is None or
            self.image_label.point2 is None or
            self.image_label.image_array is None):
            self.band_preview_label.update_band_image(None)
            return
        channel_mode = self.channel_combo.currentText()
        if self.image_label.image_array.ndim == 2:
            img_for_band = self.image_label.image_array
        else:
            img_for_band = extract_channel(self.image_label.image_array, channel_mode)
        p1 = self.image_label.point1
        p2 = self.image_label.point2
        bw = self.image_label.bandwidth
        length = int(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))
        if length == 0:
            self.band_preview_label.update_band_image(None)
            return
        xs = np.linspace(p1[0], p2[0], length)
        ys = np.linspace(p1[1], p2[1], length)
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        seg_len = np.hypot(dx, dy)
        if seg_len == 0:
            self.band_preview_label.update_band_image(None)
            return
        perp_x = dy / seg_len
        perp_y = -dx / seg_len
        half_band = bw // 2
        band_section = np.zeros((length, 2 * half_band + 1), dtype=np.uint8)
        for i in range(length):
            cx = xs[i]
            cy = ys[i]
            for offset in range(-half_band, half_band + 1):
                bx = int(cx + perp_x * offset)
                by = int(cy + perp_y * offset)
                if 0 <= bx < img_for_band.shape[1] and 0 <= by < img_for_band.shape[0]:
                    band_section[i, offset + half_band] = img_for_band[by, bx]
                else:
                    band_section[i, offset + half_band] = 0
        band_section_T = band_section.T
        self.band_preview_label.update_band_image(band_section_T)

    def update_magnifiers(self):
        img = self.image_label.image_array
        if img is None:
            self.mag1_label.clear()
            self.mag2_label.clear()
            return
        if self.image_label.point1 is not None:
            self.mag1_label.update_magnifier(img, self.image_label.point1, zoom=4)
        else:
            self.mag1_label.clear()
        if self.image_label.point2 is not None:
            self.mag2_label.update_magnifier(img, self.image_label.point2, zoom=4)
        else:
            self.mag2_label.clear()

    def calculate_profile(self):
        if (self.image_label.image_array is None or
            self.image_label.point1 is None or
            self.image_label.point2 is None):
            QMessageBox.warning(self, "Warning", "No segment defined or no image loaded.")
            return
        channel_mode = self.channel_combo.currentText()
        if self.image_label.image_array.ndim == 2:
            img_for_calc = self.image_label.image_array
        else:
            img_for_calc = extract_channel(self.image_label.image_array, channel_mode)
        p1 = self.image_label.point1
        p2 = self.image_label.point2
        bw = self.image_label.bandwidth
        length = int(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))
        if length == 0:
            QMessageBox.warning(self, "Warning", "Segment length is zero!")
            return
        xs = np.linspace(p1[0], p2[0], length)
        ys = np.linspace(p1[1], p2[1], length)
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        seg_len = np.hypot(dx, dy)
        if seg_len == 0:
            QMessageBox.warning(self, "Warning", "Segment length is zero!")
            return
        perp_x = dy / seg_len
        perp_y = -dx / seg_len
        half_band = bw // 2
        raw_means = np.zeros(length, dtype=np.float64)
        raw_stds  = np.zeros(length, dtype=np.float64)
        band_section = np.zeros((length, 2 * half_band + 1), dtype=np.uint8)
        for i in range(length):
            cx = xs[i]
            cy = ys[i]
            band_vals = []
            for offset in range(-half_band, half_band + 1):
                bx = int(cx + perp_x * offset)
                by = int(cy + perp_y * offset)
                if 0 <= bx < img_for_calc.shape[1] and 0 <= by < img_for_calc.shape[0]:
                    val = img_for_calc[by, bx]
                    band_vals.append(val)
                    band_section[i, offset + half_band] = val
                else:
                    band_vals.append(0)
                    band_section[i, offset + half_band] = 0
            if band_vals:
                raw_means[i] = np.mean(band_vals)
                raw_stds[i]  = np.std(band_vals)
            else:
                raw_means[i] = 0
                raw_stds[i]  = 0
        bin_size = self.bin_spin.value()
        n_bins = length // bin_size
        x_down = []
        mean_down = []
        std_down  = []
        band_min  = []
        band_max  = []
        for i in range(n_bins):
            start_i = i * bin_size
            end_i   = start_i + bin_size
            chunk_mean = raw_means[start_i:end_i]
            chunk_std  = raw_stds[start_i:end_i]
            sub_section= band_section[start_i:end_i, :]
            if len(chunk_mean) == 0:
                continue
            chunkX     = (i + 0.5)*bin_size
            block_mean = np.mean(chunk_mean)
            block_std  = np.mean(chunk_std)
            x_down.append(chunkX)
            mean_down.append(block_mean)
            std_down.append(block_std)
            sub_min = np.min(sub_section)
            sub_max = np.max(sub_section)
            band_min.append(sub_min)
            band_max.append(sub_max)
        x_down    = np.array(x_down)
        mean_down = np.array(mean_down)
        std_down  = np.array(std_down)
        band_min  = np.array(band_min)
        band_max  = np.array(band_max)
        fig, (ax_profile, ax_band) = plt.subplots(2, 1, figsize=(8, 6),
                                                 gridspec_kw={'height_ratios':[3,1]})
        ax_profile.set_title(self.title_edit.text())
        ax_profile.set_xlabel(self.xlabel_edit.text())
        ax_profile.set_ylabel(self.ylabel_edit.text())
        mean_color_choice = self.mean_line_color_combo.currentText()
        mean_color = LINE_COLOR_MAP[mean_color_choice]
        mean_style_choice = self.mean_line_style_combo.currentText()
        mean_style = LINE_STYLE_MAP[mean_style_choice]
        mean_thick = self.mean_line_thick_spin.value()
        mean_marker_choice = self.mean_marker_combo.currentText()
        marker_style = MARKER_MAP[mean_marker_choice]
        marker_size  = self.mean_marker_size_spin.value()
        if mean_thick == 0:
            line_kwargs = dict(linewidth=0)
        else:
            line_kwargs = dict(linewidth=mean_thick, linestyle=mean_style)
        ax_profile.plot(
            x_down, mean_down,
            color=mean_color,
            marker=marker_style,
            markersize=marker_size,
            **line_kwargs,
            label="Mean intensity"
        )
        if self.show_errorbar_checkbox.isChecked():
            ax_profile.errorbar(
                x_down, mean_down,
                yerr=std_down,
                fmt='none',
                ecolor='gray',
                elinewidth=1.0,
                capsize=3,
                label='± Std dev'
            )
        if self.show_minmax_checkbox.isChecked():
            min_color = LINE_COLOR_MAP[self.min_line_color_combo.currentText()]
            min_style = LINE_STYLE_MAP[self.min_line_style_combo.currentText()]
            min_thick = self.min_line_thick_spin.value()
            max_color = LINE_COLOR_MAP[self.max_line_color_combo.currentText()]
            max_style = LINE_STYLE_MAP[self.max_line_style_combo.currentText()]
            max_thick = self.max_line_thick_spin.value()
            ax_profile.plot(x_down, band_min, color=min_color, linestyle=min_style,
                            linewidth=min_thick, label='Min (band)')
            ax_profile.plot(x_down, band_max, color=max_color, linestyle=max_style,
                            linewidth=max_thick, label='Max (band)')
        ax_profile.grid(self.show_profile_grid_checkbox.isChecked())
        ax_profile.legend()
        band_section_T = band_section.T
        extent = [0, length, -half_band, half_band]
        ax_band.imshow(band_section_T, cmap='gray', aspect='auto',
                       extent=extent, origin='upper')
        band_title = self.band_title_edit.text()
        band_xlabel = self.band_xlabel_edit.text()
        band_ylabel = self.band_ylabel_edit.text()
        ax_band.set_title(band_title)
        ax_band.set_xlabel(band_xlabel)
        ax_band.set_ylabel(band_ylabel)
        ax_profile.set_xlim(0, length)
        ax_band.set_xlim(0, length)
        ax_band.grid(self.show_band_grid_checkbox.isChecked())
        if self.show_centerline_checkbox.isChecked():
            center_c = LINE_COLOR_MAP[self.center_color_combo.currentText()]
            center_s = LINE_STYLE_MAP[self.center_style_combo.currentText()]
            center_w = self.center_thick_spin.value()
            ax_band.hlines(y=0, xmin=0, xmax=length,
                           color=center_c, linestyle=center_s, linewidth=center_w)
        plt.tight_layout()
        plt.show()

    def calculate_multi_channel_profile(self):
        if (self.image_label.image_array is None or
            self.image_label.point1 is None or
            self.image_label.point2 is None):
            QMessageBox.warning(self, "Warning", "No segment defined or no image loaded.")
            return
        channel_list = ["Red", "Green", "Blue", "Gray"]
        if self.image_label.image_array.ndim == 2:
            channel_list = ["Gray", "Gray", "Gray", "Gray"]
        p1 = self.image_label.point1
        p2 = self.image_label.point2
        bw = self.image_label.bandwidth
        length = int(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))
        if length == 0:
            QMessageBox.warning(self, "Warning", "Segment length is zero!")
            return
        xs = np.linspace(p1[0], p2[0], length)
        ys = np.linspace(p1[1], p2[1], length)
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        seg_len = np.hypot(dx, dy)
        if seg_len == 0:
            QMessageBox.warning(self, "Warning", "Segment length is zero!")
            return
        perp_x = dy / seg_len
        perp_y = -dx / seg_len
        bin_size = self.bin_spin.value()
        half_band = bw // 2
        fig, axes = plt.subplots(2, 4, figsize=(16, 6), gridspec_kw={'height_ratios':[3,1]})
        channel_names = ["R", "G", "B", "Gray"]
        for i, ch in enumerate(channel_list):
            if self.image_label.image_array.ndim == 2:
                img_for_calc = self.image_label.image_array
            else:
                img_for_calc = extract_channel(self.image_label.image_array, ch)
            band_section = np.zeros((length, 2*half_band+1), dtype=np.uint8)
            raw_means = np.zeros(length, dtype=np.float64)
            raw_stds  = np.zeros(length, dtype=np.float64)
            for j in range(length):
                cx = xs[j]
                cy = ys[j]
                band_vals = []
                for offset in range(-half_band, half_band+1):
                    bx = int(cx + perp_x*offset)
                    by = int(cy + perp_y*offset)
                    if 0 <= bx < img_for_calc.shape[1] and 0 <= by < img_for_calc.shape[0]:
                        val = img_for_calc[by, bx]
                        band_vals.append(val)
                        band_section[j, offset+half_band] = val
                    else:
                        band_vals.append(0)
                        band_section[j, offset+half_band] = 0
                if band_vals:
                    raw_means[j] = np.mean(band_vals)
                    raw_stds[j]  = np.std(band_vals)
                else:
                    raw_means[j] = 0
                    raw_stds[j]  = 0
            n_bins = length // bin_size
            x_down = []
            mean_down = []
            std_down  = []
            for j in range(n_bins):
                start_j = j*bin_size
                end_j   = start_j+bin_size
                chunk_mean = raw_means[start_j:end_j]
                chunk_std  = raw_stds[start_j:end_j]
                if len(chunk_mean)==0:
                    continue
                chunkX = (j+0.5)*bin_size
                block_mean = np.mean(chunk_mean)
                block_std  = np.mean(chunk_std)
                x_down.append(chunkX)
                mean_down.append(block_mean)
                std_down.append(block_std)
            x_down = np.array(x_down)
            mean_down= np.array(mean_down)
            std_down = np.array(std_down)
            ax_profile = axes[0, i]
            ax_profile.set_title(f"{channel_names[i]} Channel")
            color_for_ch = channel_names[i].lower() if channel_names[i]!="Gray" else "black"
            ax_profile.plot(x_down, mean_down, color=color_for_ch,
                            label=f"{channel_names[i]} mean")
            if self.show_errorbar_checkbox.isChecked():
                ax_profile.errorbar(x_down, mean_down, yerr=std_down, fmt='none', ecolor='gray',
                                    elinewidth=1.0, capsize=3)
            ax_profile.grid(self.show_profile_grid_checkbox.isChecked())
            band_section_T = band_section.T
            ax_band = axes[1, i]
            ax_band.imshow(band_section_T, cmap='gray', aspect='auto',
                           extent=[0, length, -half_band, half_band],
                           origin='upper')
            ax_band.set_title(f"{channel_names[i]} Band")
            ax_band.grid(self.show_band_grid_checkbox.isChecked())
        plt.tight_layout()
        plt.show()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
