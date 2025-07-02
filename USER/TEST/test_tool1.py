# test_tool1.py

import sys
from PyQt5.QtWidgets import QApplication
from tools.tool1_ui import Tool1UI

app = QApplication(sys.argv)
win = Tool1UI()
win.show()
sys.exit(app.exec_())