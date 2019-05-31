"""A simple aplication to label images of faces."""
import sys
import json
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets


def read_json(fname):
    with open(fname) as fid:
        data = json.load(fid)
    return data


class Marker(QtWidgets.QGraphicsPolygonItem):
    def __init__(self, parent=None):
        super(Marker, self).__init__(parent)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setZValue(10)
        p = [QtCore.QPointF(-10., -10.), QtCore.QPointF(10., -10.),
             QtCore.QPointF(10., 10.), QtCore.QPointF(-10., 10.)]
        self.setPolygon(QtGui.QPolygonF(p))
        self.setPen(QtGui.QPen(QtGui.QColor("Green"), 0.5))
        self.setBrush(QtGui.QColor(255, 0, 0, 128))


class imageLabeler(QtWidgets.QMainWindow):
    """The main application window with menu items."""

    def __init__(self):
        super(imageLabeler, self).__init__()
        self.viewer = ImageView(self)
        self.setCentralWidget(self.viewer)
        self.createMenus()
        self.setWindowTitle("Face Label Tool (FLT)")
        self.resize(800, 800)
        self.viewer.scene.addItem(Marker())

    def about(self):
        msg = """Face Label Tool Help:"""
        QtWidgets.QMessageBox.about(
            self, "About Image Viewer", msg)

    def createMenus(self):
        self.openAct = QtWidgets.QAction(
            "Open...", self, shortcut="Ctrl+O", triggered=self.open_image)
        self.exitAct = QtWidgets.QAction(
            "Exit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.aboutAct = QtWidgets.QAction(
            "About", self, triggered=self.about)
        self.fitAct = QtWidgets.QAction(
            "Fit to view", self, shortcut="Ctrl+F",
            triggered=self.viewer.fitInView)

        self.fileMenu = QtWidgets.QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QtWidgets.QMenu("&View", self)
        self.viewMenu.addAction(self.fitAct)

        self.helpMenu = QtWidgets.QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)

        # self.menuBar().setNativeMenuBar(False)
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def open_landmarks(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Landmark FIle", QtCore.QDir.currentPath())
        if not fname:
            return
        self.landmarks = read_json(fname)

    def open_image(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Image", QtCore.QDir.currentPath())
        if not fname:
            return

        image = QtGui.QImage(fname)
        if image.isNull():
            QtWidgets.QMessageBox.information(
                self, "Image Viewer", "Cannot load %s." % fname)
            return
        self.viewer.setPhoto(QtGui.QPixmap.fromImage(image))

# -----------------------------------------------------------------------------
# Graphics View
# -----------------------------------------------------------------------------


class ImageView(QtWidgets.QGraphicsView):

    def __init__(self, parent):
        super(ImageView, self).__init__(parent)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.photo = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.photo)
        self.setScene(self.scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self.photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
        self.resetTransform()
        self.scale(1.0, 1.0)

    def setPhoto(self, pixmap=None):
        if pixmap and not pixmap.isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self.photo.setPixmap(pixmap)
        else:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.photo.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
        else:
            factor = 0.8
        self.scale(factor, factor)

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self.photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)


if __name__ == '__main__':
    app = QtWidgets.QApplication(["Face Label Tool"])
    imageLabeler = imageLabeler()
    imageLabeler.show()
    sys.exit(app.exec_())
