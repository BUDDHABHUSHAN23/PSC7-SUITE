# test_tool2.py
import sys
from PyQt5.QtWidgets import QApplication
from tools.tool2_ui import Tool2UI

app = QApplication(sys.argv)
win = Tool2UI()
win.show()
sys.exit(app.exec_())
