"""A simple aplication to label images of faces."""
import sys
import json
import numpy as np
from PyQt5.QtCore import QDir, Qt, QPoint, QPointF, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QImage, QPainter, QPalette, QPixmap, QBrush, QColor,
    QPolygonF, QPen)
from PyQt5.QtWidgets import (
    QAction, QApplication, QFileDialog, QLabel, QMainWindow, QMenu,
    QMessageBox, QScrollArea, QSizePolicy, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QFrame, QGraphicsItem)


def read_json(fname):
    with open(fname) as fid:
        data = json.load(fid)
    return data


def place_holder():
    h, w, c = 200, 200, 3
    img = np.ones([h, w, c], dtype=np.uint8) * 32
    bytesPerLine = 3 * w
    qimg = QImage(img.data, w, h, bytesPerLine, QImage.Format_RGB888)
    return QPixmap(qimg)


def test_poly(scene):
    points = QPolygonF()
    points.append(QPointF(-10., -10.))
    points.append(QPointF(10., -10.))
    points.append(QPointF(10., 10.))
    points.append(QPointF(-10., 10.))
    poly = scene.addPolygon(points, QPen(QColor(255, 128, 0), 0.5,
                                         Qt.SolidLine, Qt.RoundCap,
                                         Qt.RoundJoin),
                            QBrush(QColor(255, 0, 0, 128)))
    poly.setFlag(QGraphicsItem.ItemIsSelectable)
    poly.setFlag(QGraphicsItem.ItemIsMovable)


class imageLabeler(QMainWindow):
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
        QMessageBox.about(
            self, "About Image Viewer", msg)

    def createMenus(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O",
                               triggered=self.open_image)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                               triggered=self.close)
        self.aboutAct = QAction("&About", self, triggered=self.about)

        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.helpMenu)

    def open_landmarks(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Landmark FIle",
                                               QDir.currentPath())
        if not fname:
            return
        self.landmarks = read_json(fname)

    def open_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Image",
                                               QDir.currentPath())
        if not fname:
            return

        image = QImage(fname)
        if image.isNull():
            QMessageBox.information(self, "Image Viewer",
                                    "Cannot load %s." % fname)
            return
        self.viewer.setPhoto(QPixmap.fromImage(image))
        # self.p_image.setPixmap(QPixmap.fromImage(image))
        self.scaleFactor = 1.0
        # for i in self.viewer.scene.items():
        #     print(i.pos().x(), i.pos().y())


# -----------------------------------------------------------------------------
# Graphics View
# -----------------------------------------------------------------------------


class ImageView(QGraphicsView):
    photoClicked = pyqtSignal(QPoint)

    def __init__(self, parent):
        super(ImageView, self).__init__(parent)
        self.zoom = 0
        self.empty = True
        self.scene = QGraphicsScene(self)
        self.photo = QGraphicsPixmapItem()
        self.photo.setZValue(-1)
        self.scene.addItem(self.photo)
        self.setScene(self.scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.NoFrame)

    def hasPhoto(self):
        return not self.empty

    def fitInView(self, scale=True):
        rect = QRectF(self.photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
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
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.photo.setPixmap(pixmap)
        else:
            self.empty = True
            self.setDragMode(QGraphicsView.NoDrag)
            self.photo.setPixmap(QPixmap())
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
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.setDragMode(QGraphicsView.NoDrag)
        elif not self.photo.pixmap().isNull():
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self.photo.isUnderMouse():
            self.photoClicked.emit(QPoint(event.pos()))
        super(ImageView, self).mousePressEvent(event)


if __name__ == '__main__':
    app = QApplication(["Face Label Tool"])
    imageLabeler = imageLabeler()
    imageLabeler.show()
    sys.exit(app.exec_())
