#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试消息气泡显示
"""

import sys
import os
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

# 设置样式
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

app = QGuiApplication(sys.argv)
engine = QQmlApplicationEngine()

qml_file = Path(__file__).parent / "qml" / "TestBubble.qml"
engine.load(QUrl.fromLocalFile(str(qml_file)))

if not engine.rootObjects():
    print("❌ 加载失败")
    sys.exit(-1)

print("✅ 测试气泡已加载")
sys.exit(app.exec())
