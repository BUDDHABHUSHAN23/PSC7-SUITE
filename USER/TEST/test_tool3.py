# test_tool3.py
import sys
from PyQt5.QtWidgets import QApplication
from tools.tool3_ui import Tool3UI

app = QApplication(sys.argv)
win = Tool3UI()
win.show()
sys.exit(app.exec_())
