import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import matplotlib.image as mpimg

# Load image from disk and reorient it for viewing

fname = 'R0000187.JPG'    # This can be any photo image file
photo=np.array(mpimg.imread(fname))
photo = photo.transpose()
# select for red color and extract as monochrome image
img = photo[0,:,:]  # WHAT IF I WANT TO DISPLAY THE ORIGINAL RGB IMAGE?

# Create app
app = QtGui.QApplication([])

## Create window with ImageView widget
win = QtGui.QMainWindow()
win.resize(1200,800)
imv = pg.ImageView()
win.setCentralWidget(imv)
win.show()
win.setWindowTitle(fname)


    ## Display the data
imv.setImage(img)

def click(event):
    event.accept()
    pos = event.pos()
    print (int(pos.x()),int(pos.y()))

imv.getImageItem().mouseClickEvent = click

    ## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()