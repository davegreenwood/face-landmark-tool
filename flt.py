"""A simple aplication to label images of faces."""
import sys
import json
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets


def read_json(fname):
    with open(fname) as fid:
        data = json.load(fid)
    return data


def place_holder():
    h, w, c = 200, 200, 3
    img = np.ones([h, w, c], dtype=np.uint8) * 32
    _bytes = 3 * w
    qimg = QtGui.QImage(img.data, w, h, _bytes, QtGui.QImage.Format_RGB888)
    return QtGui.QPixmap(qimg)


def test_poly(scene):
    points = QtGui.QPolygonF()
    points.append(QtCore.QPointF(-10., -10.))
    points.append(QtCore.QPointF(10., -10.))
    points.append(QtCore.QPointF(10., 10.))
    points.append(QtCore.QPointF(-10., 10.))
    poly = scene.addPolygon(points,
                            QtGui.QPen(
                                QtGui.QColor(255, 128, 0), 0.5,
                                QtCore.Qt.SolidLine,
                                QtCore.Qt.RoundCap,
                                QtCore.Qt.RoundJoin),
                            QtGui.QBrush(QtGui.QColor(255, 0, 0, 128)))
    poly.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
    poly.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)


class imageLabeler(QtWidgets.QMainWindow):
    """The main application window with menu items."""

    def __init__(self):
        super(imageLabeler, self).__init__()
        self.viewer = ImageView(self)
        self.setCentralWidget(self.viewer)
        self.createMenus()
        self.setWindowTitle("Face Label Tool (FLT)")
        self.resize(800, 800)
        test_poly(self.viewer.scene)

    def about(self):
        msg = """Face Label Tool Help:"""
        QtWidgets.QMessageBox.about(
            self, "About Image Viewer", msg)

    def createMenus(self):
        self.openAct = QtWidgets.QAction(
            "&Open...", self, shortcut="Ctrl+O", triggered=self.open_image)
        self.exitAct = QtWidgets.QAction(
            "E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.aboutAct = QtWidgets.QAction("&About", self, triggered=self.about)

        self.fileMenu = QtWidgets.QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.helpMenu = QtWidgets.QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)

        self.menuBar().addMenu(self.fileMenu)
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
        # self.p_image.setPixmap(QtGui.QPixmap.fromImage(image))
        self.scaleFactor = 1.0
        # for i in self.viewer.scene.items():
        #     print(i.pos().x(), i.pos().y())


# -----------------------------------------------------------------------------
# Graphics View
# -----------------------------------------------------------------------------


class ImageView(QtWidgets.QGraphicsView):
    # photoClicked = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, parent):
        super(ImageView, self).__init__(parent)
        self.zoom = 0
        self.empty = True
        self.scene = QtWidgets.QGraphicsScene(self)
        self.photo = QtWidgets.QGraphicsPixmapItem()
        self.photo.setZValue(-1)
        self.scene.addItem(self.photo)
        self.setScene(self.scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def hasPhoto(self):
        return not self.empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self.photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self.zoom = 0

    def setPhoto(self, pixmap=None):
        self.zoom = 0
        if pixmap and not pixmap.isNull():
            self.empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self.photo.setPixmap(pixmap)
        else:
            self.empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.photo.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
            self.zoom += 1
        else:
            factor = 0.8
            self.zoom -= 1
        if self.zoom > 0:
            self.scale(factor, factor)
        elif self.zoom == 0:
            self.fitInView()
        else:
            self.zoom = 0

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self.photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    # def mousePressEvent(self, event):
    #     if self.photo.isUnderMouse():
    #         self.photoClicked.emit(QPoint(event.pos()))
    #     super(ImageView, self).mousePressEvent(event)


if __name__ == '__main__':
    app = QtWidgets.QApplication(["Face Label Tool"])
    imageLabeler = imageLabeler()
    imageLabeler.show()
    sys.exit(app.exec_())
