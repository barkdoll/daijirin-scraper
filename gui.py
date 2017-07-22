import sys
from PyQt5 import QtWidgets, QtGui


class Window():
   app = QtWidgets.QApplication(sys.argv)
   w = QtWidgets.QWidget()

   vBox = QtWidgets.QVBoxLayout()
   vBox.addWidget(w)

   hBox = QtWidgets.QHBoxLayout()
   hBox.addLayout(vBox)

   w.setGeometry(50,50,800,300)
   w.setWindowTitle('Daijirin Definition Grabber')
   w.setWindowIcon(QtGui.QIcon('daijiscrape/icon.png'))
   w.show()
   sys.exit(app.exec_())

Window()