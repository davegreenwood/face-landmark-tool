"""A simple aplication to label images of faces."""
import sys
import json
import numpy as np
from pkg_resources import resource_filename
from PyQt5 import QtCore, QtGui, QtWidgets


def read_json(fname):
    with open(fname) as fid:
        data = json.load(fid)
    return data


class Group(QtWidgets.QGraphicsItem):
    """https://stackoverflow.com/a/32198716"""

    def __init__(self, parent=None):
        super(Group, self).__init__(parent)
        self.line_col = QtGui.QColor(0, 255, 0)
        self.pen = QtGui.QPen(self.line_col, 0.5)
        self.rect = QtCore.QRectF()
        m1 = Marker(parent=self)
        m2 = Marker(parent=self)
        m2.setPos(20, 30)
        self.markers = [m1, m2]
        self.polyline = QtGui.QPolygonF()
        self.setpolyline()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setZValue(10)

    def boundingRect(self):
        return self.rect

    def paint(self, painter=None, style=None, widget=None):
        painter.setPen(self.pen)
        painter.drawPolyline(self.polyline)

    def setpolyline(self):
        self.polyline.clear()
        x, y = [], []
        for m in self.markers:
            p = m.pos()
            x.append(p.x())
            y.append(p.y())
            self.polyline.append(p)
        self.rect = QtCore.QRectF(
            min(x) - 6, min(y) - 6,
            max(x) - min(x) + 6,
            max(y) - min(y) + 6)


class Marker(QtWidgets.QGraphicsObject):
    """
    Draggable - https://stackoverflow.com/a/28519324
    """

    def __init__(self, parent=None):
        super(Marker, self).__init__(parent)
        self.parent = parent
        self.fill_col = QtGui.QColor(0, 255, 0, 50)
        self.line_col = QtGui.QColor(0, 255, 0)
        self.pen = QtGui.QPen(self.line_col, 0.5)
        self.rect = QtCore.QRectF(-6, -6, 12, 12)
        self.line1 = QtCore.QLineF(0, 0, 0, 5)
        self.line2 = QtCore.QLineF(0, 0, 0, -5)
        self.line3 = QtCore.QLineF(0, 0, 5, 0)
        self.line4 = QtCore.QLineF(0, 0, -5, 0)
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setZValue(10)

    def boundingRect(self):
        return self.rect

    def paint(self, painter=None, style=None, widget=None):
        painter.setPen(self.pen)
        for line in [self.line1, self.line2, self.line3, self.line4]:
            painter.drawLine(line)
        painter.fillRect(self.rect, self.fill_col)

    def mouseMoveEvent(self, event):
        if (QtCore.QLineF(
            QtCore.QPointF(event.screenPos()),
            QtCore.QPointF(event.buttonDownScreenPos(
                QtCore.Qt.LeftButton))).length() <
                QtWidgets.QApplication.startDragDistance()):
            return
        if self.parent:
            self.parent.setpolyline()
        drag = QtGui.QDrag(event.widget())
        drag.exec_()
        self.setCursor(QtCore.Qt.OpenHandCursor)
        super(Marker, self).mouseMoveEvent(event)

    def mousePressEvent(self, event):
        self.setCursor(QtCore.Qt.ClosedHandCursor)
        super(Marker, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(QtCore.Qt.OpenHandCursor)
        super(Marker, self).mouseReleaseEvent(event)


class imageLabeler(QtWidgets.QMainWindow):
    """The main application window with menu items."""

    def __init__(self):
        super(imageLabeler, self).__init__()
        self.viewer = ImageView(self)
        self.setCentralWidget(self.viewer)
        self.createMenus()
        self.setWindowTitle("Face Label Tool (FLT)")
        self.resize(800, 800)
        self.show()

    def about(self):
        msg = """Face Label Tool Help:"""
        QtWidgets.QMessageBox.about(self, "About Image Viewer", msg)

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

        self.fileMenu = QtWidgets.QMenu("File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QtWidgets.QMenu("View", self)
        self.viewMenu.addAction(self.fitAct)

        self.helpMenu = QtWidgets.QMenu("Help", self)
        self.helpMenu.addAction(self.aboutAct)

        self.menuBar().setNativeMenuBar(True)
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
        self.image = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.image)
        self.scene.addItem(Group())
        self.setScene(self.scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self.image.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
        self.resetTransform()
        self.scale(1.0, 1.0)

    def setPhoto(self, pixmap=None):
        if pixmap and not pixmap.isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self.image.setPixmap(pixmap)
        else:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.image.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
        else:
            factor = 0.8
        self.scale(factor, factor)

    # def mousePressEvent(self, event):
    #     self.setCursor(QtCore.Qt.ClosedHandCursor)

    # def mouseReleaseEvent(self, event):
    #     self.setCursor(QtCore.Qt.OpenHandCursor)

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self.image.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)


if __name__ == '__main__':
    app = QtWidgets.QApplication(["Face Label Tool"])
    path = resource_filename(__name__, "icon.png")
    app.setWindowIcon(QtGui.QIcon(path))
    ui = imageLabeler()
    sys.exit(app.exec_())
