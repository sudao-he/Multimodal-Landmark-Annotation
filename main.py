import numpy as np
from PyQt5.uic import loadUi
import sys
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QBrush, QFont, QImage
from PyQt5.QtCore import Qt, QPoint
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QApplication, QAbstractItemView, QVBoxLayout, QMessageBox, QInputDialog, QFileDialog
, QMainWindow)
import os
import scipy.io as sio
from scipy.io import loadmat
import json
import base64
import h5py
import math
import cv2

from Frame import Ui_MainWindow   # 静态加载 UI 文件

# 用python代码模拟键盘输入。原本想解决的问题是QListWidget会使键盘监听失败，按一下Alt键会恢复监听。这里的作用就是模拟键盘按下Alt键   https://cloud.tencent.com/developer/article/1566445
# import win32api  
# import win32con
# win32api.keybd_event(18,0,0,0)  # Alt的键号是18
# win32api.keybd_event(18,0,win32con.KEYEVENTF_KEYUP,0)


class MyMainForm(QMainWindow ,Ui_MainWindow):     # 静态加载 UI 文件
# class MyMainForm(QMainWindow):                 # 动态加载 UI 文件
    def __init__(self, imageDir='', imageDir_2='', outDir='', offset=10):
        super(MyMainForm ,self).__init__()
        
        # 静态加载 UI 文件（将ui文件转化为python文件）
        self.setupUi(self)
        
        # #动态加载 UI 文件
        # loadUi("./ui.ui", self)  #加载UI文件到self

        
        # 设置图标
        self.setWindowIcon(QIcon('logo.ico'))

        # 设置标题
        self.setWindowTitle('Landmarks Annotation Tool')

        
        # 获取电脑屏幕的尺寸
        desktop_height = QApplication.desktop().screenGeometry().height()
        desktop_width  = QApplication.desktop().screenGeometry().width()


        # self.setFixedSize(desktop_width, desktop_height )   # 固定窗口大小
        # self.setStyleSheet('background-color:#2C3E50;')     # 背景颜色填充
        self.layout_width = math.floor((desktop_width - 100 - 220) / 2)  # 右侧给出220的像素区域用来放置按钮、listbox之类的控件
        self.layout_height = math.floor((desktop_height - 100 - 80))  # 下方给出80的像素区域用来放置导航栏

        # 坑：如果是建立的界面是QWidget类的，就只需要加下面的第三句，就可以实现鼠标不按下也能跟随 ； 如果是建立的界面是QMainWindow类的，只用第三句没有效果，需要用下面的三条语句在一块才可以
        # setCentralWidget是函数，centralwidget可以在ui文件里找到。     
        # https://www.codeleading.com/article/20072274463/
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setMouseTracking(True)
        self.setMouseTracking(True)

        # 坑：当Qt的控件QListWidget或QTableView嵌入到主窗口之后，他本身也会接受按键事件，所以获得焦点时，按键点击并不会触发主窗口的keyPressEvent()函数，也就是说监听冲突了    #
        # 解决方法就是添加下面这一句，让其不处理按键事件。也可以在qtdesigner中设置，选中这个这个控件后，右侧的属性编辑器里面有一项是focusPolicy，选择NoFocus即可    
        # https://blog.csdn.net/u010189457/article/details/53149805
        self.listWidget.setFocusPolicy(Qt.NoFocus)

        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)  # 设置之后可以通过【Ctrl+鼠标】左键实现QListWidget的多选
        self.listWidget.clicked.connect(self.Preview)  # clicked:当双击某项时，信号被发射。      激活预览动作
        self.listWidget.doubleClicked.connect(self.Delete)  # doubleClicked:当双击某项时，信号被发射。激活删除动作

        self.listWidget_2.setFocusPolicy(Qt.NoFocus)

        self.listWidget_2.setSelectionMode(QAbstractItemView.ExtendedSelection)  # 设置之后可以通过【Ctrl+鼠标】左键实现QListWidget的多选
        self.listWidget_2.clicked.connect(self.Preview_2)  # clicked:当双击某项时，信号被发射。      激活预览动作
        self.listWidget_2.doubleClicked.connect(self.Delete_2)

        # 三个按钮的触发函数
        self.format.clicked.connect(self.get_format)
        self.format.setToolTip(
            '<b>json</b>：生成的格式同labelme<hr>     <b>txt </b>：每行的坐标用逗号隔开')  # 鼠标停留时显示提示性文字
        self.input.clicked.connect(self.click_input_dir)
        self.input_2.clicked.connect(self.click_input_dir_2)
        self.output.clicked.connect(self.click_output_dir)

        # 关于页码的触发函数
        self.Prev.clicked.connect(self.prevImage)
        self.Next.clicked.connect(self.nextImage)
        self.go.clicked.connect(self.gotoImage)
        self.add_rgb_corners.clicked.connect(self.detect_corners)

        # # 菜单栏的触发函数
        # self.actioninstructions.triggered.connect(self.instructions)   # 这里用triggered，而不是clicked   详情：https://www.cnblogs.com/unixcs/p/14272631.html
        # self.actionabout.triggered.connect(self.about)        
        # def instructions(self):
        #     QMessageBox.information(self,"Infomation","1. 选择标签格式（默认为mat）\n2. 选择图片的输入目录\n3. 选择标签的输出目录")
        # def about(self):
        #     QMessageBox.information(self,"Infomation","作者:hsy 版权所有 请勿商业使用")

        self.pos_xy = []
        self.preview_flag = False
        self.preview_flag_2 = False
        self.img = None
        self.labelpath = ''
        self.imagepath = ''
        self.imageDir = imageDir
        self.imageDir_2 = imageDir_2
        self.outDir = outDir
        self.cur = 0
        self.total = 0
        self.offset = offset
        self.label_format = 'mat'
        self.checkboard_row = 11
        self.checkboard_column = 8

        # 这个是滚轮放缩导致的等比尺度缩放，是一直变换的，可能小于1可能等于1也能能大于1，要和ori_scale区分开来。     只有滚轮滑动才会更新ratio
        # ori_scale图片是刚被加载到界面上，为了不越界，而做的一个等比缩小尺度，是恒定的，可能等于1，也可能小于1，不会大于1
        self.ratio = 1
        if imageDir != '':
            self.open_input_dir(input_dir=imageDir)
        if imageDir_2 != '':
            self.open_input_dir_2(input_dir=imageDir_2)
        if outDir != '':
            self.open_output_dir(input_dir=outDir)
        self.Load()

    '''
    前面提到：允许图片的最大放置尺寸为【屏幕高-80（其实还要再减去一个窗口上边框，这里就认为边框是一条细线） , 屏幕宽-220】，任何一张导入的图片，都是从左上角开始铺设，现在要处理的就是两条边是否越界，如果越界，两条边做等比缩小，做如下分析：
      如果该图宽和高都没有超过被允许的最大尺寸，那么图像的左上角就正常放置在屏幕的左上角，空间是足够的，不用进行处理，所以ori_scale=1
      如果该图的宽没有超过被允许的最大尺寸，但高越界了，就让高缩小到被允许的最大高度，记录缩小的比例，让宽也等比缩小，这个比例赋值给ori_scale，说明图像刚被导入进来的时候就被等比缩小了
      如果该图的高没有超过被允许的最大尺寸，但宽越界了，就让宽缩小到被允许的最大宽度，记录缩小的比例，让高也等比缩小，这个比例赋值给ori_scale，说明图像刚被导入进来的时候就被等比缩小了
      如果该图宽和高都超过了被允许的最大尺寸，那就从宽和高里挑一个超过幅度最大的，让幅度最大的缩小到它所对应的最大尺寸，另一个也做等比缩小
    '''

    def img_resize(self):
        self.img_width, self.img_height, self.ori_scale, self.x_y_scale = self.find_resize(self.img.width(), self.img.height(), self.layout_width, self.layout_height)
        self.img_2_width, self.img_2_height, self.ori_scale_2, self.x_y_scale_2 = self.find_resize(self.img_2.width(),
                                                                                             self.img_2.height(),
                                                                                             self.layout_width,
                                                                                             self.layout_height)
        # if self.img_2.width() < self.layout_width and self.img_2.height() < self.layout_height:
        #     x_ = (self.layout_width) / self.img_2.width()
        #     y_ = (self.layout_height) / self.img_2.height()
        #     if x_ > y_:
        #         self.ori_scale_2 = (self.layout_height) / self.img_2.height()
        #         self.img_2_width = int(self.img_2.width() * self.ori_scale_2)
        #         self.img_2_height = self.layout_height
        #     else:
        #         self.ori_scale_2 = (self.layout_width) / self.img_2.width()
        #         self.img_2_width = self.layout_width
        #         self.img_2_height = int(self.img_2.height() * self.ori_scale_2)
        #
        # elif self.img_2.width() < self.layout_width and self.img_2.height() >= self.layout_height:
        #     self.ori_scale_2 = (self.layout_height) / self.img_2.height()
        #     self.img_2_width = int(self.img_2.width() * self.ori_scale_2)
        #     self.img_2_height = self.layout_height
        #
        #
        # elif self.img_2.width() >= self.layout_width and self.img_2.height() < self.layout_height:
        #     self.ori_scale_2 = (self.layout_width) / self.img_2.width()
        #     self.img_2_width = self.layout_width
        #     self.img_2_height = int(self.img_2.height() * self.ori_scale_2)
        # else:
        #     x_ = self.img_2.width() / (self.layout_width)
        #     y_ = self.img_2.height() / (self.layout_height)
        #     # 寻找一个越界范围更大的
        #     if x_ > y_:
        #         self.ori_scale_2 = (self.layout_height) / self.img_2.height()
        #         self.img_2_width = int(self.img_2.width() * self.ori_scale_2)
        #         self.img_2_height = self.layout_height
        #     else:
        #         self.ori_scale_2 = (self.layout_width) / self.img_2.width()
        #         self.img_2_width = self.layout_width
        #         self.img_2_height = int(self.img_2.height() * self.ori_scale_2)
        self.scaled_img = self.img.scaled(self.img_width, self.img_height)
        self.scaled_img_2 = self.img_2.scaled(self.img_2_width, self.img_2_height)

        self.img = self.scaled_img
        self.img_2 = self.scaled_img_2  # 做一个备份，这个很重要，后面会经常用到这个备份

    # 获取用户想要的标签格式
    def get_format(self):
        items = ('mat', 'json', 'h5', 'txt')
        item, ok = QInputDialog.getItem(self, "Select label format", 'Format List', items, 0, False)
        if ok and item:
            self.label_format = item
            # 要做到在标注过程中突然变换标签格式也能动态的更新当前图片的标注状态，就得保证当前已经选完了输入和输出目录，所以这里需要判空一下
            if self.imageDir != '' and self.outDir != '':
                self.Load()

    # 打开输入目录
    def open_input_dir(self, input_dir=''):
        if input_dir == '':
            self.imageDir = QFileDialog.getExistingDirectory(self, 'Please select a folder for IR', './')
        else:
            self.imageDir = QFileDialog.getExistingDirectory(self, 'Please select a folder for IR', input_dir)
        # 判空
        if self.imageDir == '':
            QMessageBox.information(self, "Tips", "Please select a folder", QMessageBox.Yes)
            return

        # 判断该目录下有没有图片
        self.imageList = os.listdir(self.imageDir)
        self.imageList = [f for f in self.imageList if f.endswith(('.JPG', '.png', 'bmp', 'jpeg',  '.raw'))]  # 得到文件夹下指定后缀的所有文件路径

        if len(self.imageList) == 0:
            QMessageBox.information(self, "Tips", "There are no picture files in this directory", QMessageBox.Yes)
            return

        self.imageList.sort()  # 让图片粗略的按顺序导入
        self.cur = 0  # 遍历图片的游标
        self.total = len(self.imageList)  # 图片总数

    def open_input_dir_2(self, input_dir=''):
        if input_dir == '':
            self.imageDir_2 = QFileDialog.getExistingDirectory(self, 'Please select a folder for RGB', './')
        else:
            self.imageDir_2 = QFileDialog.getExistingDirectory(self, 'Please select a folder for RGB', input_dir)
        # 判空
        if self.imageDir_2 == '':
            QMessageBox.information(self, "Tips", "Please select a folder for RGB", QMessageBox.Yes)
            return

        # 判断该目录下有没有图片
        self.imageList_2 = os.listdir(self.imageDir_2)
        self.imageList_2 = [f for f in self.imageList_2 if
                            f.endswith(('.JPG', '.png', 'bmp', 'jpeg'))]  # 得到文件夹下指定后缀的所有文件路径

        if len(self.imageList_2) == 0:
            QMessageBox.information(self, "Tips", "There are no picture files in this directory", QMessageBox.Yes)
            return

        self.imageList_2.sort()  # 让图片粗略的按顺序导入
        self.cur_2 = 0  # 遍历图片的游标
        self.total_2 = len(self.imageList_2)

        if len(self.imageList_2) != len(self.imageList):
            QMessageBox.information(self, "Tips", "Number of Visual images not match IR images", QMessageBox.Yes)
            return

    # 打开输入目录
    def open_output_dir(self, input_dir=''):
        if input_dir == '':
            self.outDir = QFileDialog.getExistingDirectory(self, 'Please select a folder for output', './')
        else:
            self.outDir = QFileDialog.getExistingDirectory(self, 'Please select a folder for output', input_dir)
        # 判空
        if self.outDir == '':
            QMessageBox.information(self, "Tips", "Please select a folder for output", QMessageBox.Yes)
            return

        # 输入和输出目录都有了，直接开始导入图片和标签
        if self.imageDir != '' and self.imageDir_2 != '':
            self.Load()
        else:
            QMessageBox.information(self, "Tips", "Please select a folder for output", QMessageBox.Yes)
            return

            # 加载动作

    def Load(self):
        # 判断（防止只选择输出文件夹不选择输入文件夹）
        if self.imageDir == '':
            QMessageBox.information(self, "Tips", "Please select an input folder of IR image", QMessageBox.Yes)
            return
        if self.imageDir_2 == '':
            QMessageBox.information(self, "Tips", "Please select an input folder of RGB image", QMessageBox.Yes)
            return
        if self.outDir == '':
            QMessageBox.information(self, "Tips", "Please select an output folder", QMessageBox.Yes)
            return

        # 预处理
        self.pos_xy = []
        self.pos_xy_2 = []  # 清空后台坐标点集合
        self.listWidget.clear()
        self.listWidget_2.clear()  # 清空前端坐标点集合
        self.page.setAlignment(Qt.AlignCenter)  # 页码标签居中
        self.page.setText("%03d/%03d" % (self.cur + 1, self.total))
        self.imgName.setAlignment(Qt.AlignCenter)  # 图片名标签居中
        self.imgName.setText(self.imageList[self.cur])

        # 加载图片
        _, img_type = os.path.splitext(self.imageList[self.cur])
        if img_type == '.raw':
            img = np.fromfile(self.imageDir + '/' + self.imageList[self.cur], dtype='float32').reshape((512, 640))
            gray_img = (img - img.min()) / (img.max() - img.min()) * 255
            gray_img = gray_img.astype(np.uint8)
            color_map = cv2.applyColorMap(gray_img, cv2.COLORMAP_JET)
            self.img_ndarray = cv2.cvtColor(color_map, cv2.COLOR_BGR2RGB)
            self.img = QPixmap(QImage(self.img_ndarray.data, self.img_ndarray.shape[1], self.img_ndarray.shape[0], self.img_ndarray.shape[1] * 3, QImage.Format_RGB888))

        else:
            self.imagepath = self.imageDir + '/' + self.imageList[self.cur]
            self.img = QPixmap(self.imagepath)
        self.imagepath_2 = self.imageDir_2 + '/' + self.imageList_2[self.cur]
        self.img_2 = QPixmap(self.imagepath_2)  # 这时的self.img尺寸是原图的尺寸，还没有经过任何的放缩，先用他判断一下接下来标签中坐标点是否越界，再对他做resize

        # 加载标签
        self.labelpath = self.outDir + '/' + self.imageList[self.cur].split('.')[0] + '.' + self.label_format
        if os.path.exists(self.labelpath):
            # txt的读取方式和其他有点不一样，先单拿出来
            if self.label_format == 'txt':
                txt = open(self.labelpath)
                for line in txt:
                    x, y, x2, y2 = line.strip().split(',')  # strip()去除回车键
                    x = float(x)
                    y = float(y)
                    x2 = float(x2)
                    y2 = float(y2)
                    if 0 <= x <= self.img.width() and 0 <= y <= self.img.height():  # 过滤一下标注文件中越界的点
                        self.pos_xy.append((x, y))
                        self.pos_xy_2.append((x2, y2)) # 保存的时候用真实的位置，不四舍五入
                        self.listWidget.insertItem(len(self.listWidget),
                                                   '(' + str(round(x, 2)) + ',' + str(round(y, 2)) + ')')
                        self.listWidget_2.insertItem(len(self.listWidget_2),
                                                   '(' + str(round(x2, 2)) + ',' + str(round(y2, 2)) + ')')
            # mat、h5、json的读取方式有相同点，可以共用一小部分代码
            else:
                # 非共用部分
                if self.label_format == 'mat':
                    mat = loadmat(self.labelpath)
                    points = mat['IRPoints']
                    points_2 = mat['RGBPoints']
                elif self.label_format == 'h5':
                    h5 = h5py.File(self.labelpath, 'r')
                    points = h5['IRPoints']
                    points_2 = h5['RGBPoints']
                elif self.label_format == 'json':
                    f = open(self.labelpath, 'r')
                    content = f.read()
                    content = json.loads(content)
                    content_IR = content['shapes_IR']
                    content_RGB = content['shapes_RGB']
                    points = []
                    points_2 = []
                    for (p, p2) in zip(content_IR, content_RGB):
                        if p['points'] != []:
                            points.append(p['points'][0])
                        if p2['points'] != []:
                            points_2.append(p2['points'][0])
                # 共用部分 
                for (point, point_2) in zip(points, points_2):
                    x, y = point
                    x2, y2 = point_2
                    if 0 <= x <= self.img.width() and 0 <= y <= self.img.height():  # 过滤一下标注文件中越界的点
                        self.pos_xy.append((x, y))  # 保存的时候用真实的位置，不四舍五入
                        self.listWidget.insertItem(len(self.listWidget),
                                                   '(' + str(round(x, 2)) + ',' + str(round(y, 2)) + ')')
                        self.pos_xy_2.append((x2, y2))  # 保存的时候用真实的位置，不四舍五入
                        self.listWidget_2.insertItem(len(self.listWidget_2),
                                                   '(' + str(round(x2, 2)) + ',' + str(round(y2, 2)) + ')')

        self.img_resize()  # 最后再resize，因为加载标签的时候用到了图的尺寸来过滤一部分越界的标注点
        self.update()  # 加载完图片和标签后及时的对界面重新绘制

    # 绘制界面，由update和repaint函数调用

    # 绘制方法：
    # 1. 实例化一个 p1 = QPainter()
    # 2. p1.begin(self)
    # 3. 绘制动作
    # 4. p1.end(self)
    def paintEvent(self, event):
        # 程序刚运行时，paintEvent函数也会被执行一次，但是还没有图片被导入，drawPixmap会报错，所以这里控制一下：界面上没有图片时就不执行paintEvent函数
        if self.img == None:
            return

        p1 = QPainter()
        p1.begin(self)

        # 绘制关键点部分
        p1.drawPixmap(QPoint(0, 0), self.scaled_img)
        p1.drawPixmap(QPoint(self.layout_width + self.offset, 0, ), self.scaled_img_2)  # 将图片铺设上


        p1.setFont(QFont('Arial', 20))
        i = 1
        for pos_tmp in self.pos_xy:
            # 用画笔再画布上绘制圆点。pos_xy中的点的位置是逻辑正确的位置，但是绘制的时候，要画一个物理正确的位置，即需要跟随图片放缩。关键点加入到pos_xy时接连除了ratio和ori_scale，这里要接连乘上
            p1.setPen(QPen(QColor(255, 0, 255),
                           5 * self.ratio * self.ori_scale))  # 设置一个画笔，【5*self.ratio】代表半径，因为要考虑到标注的点的大小也要随着图片的放缩而放缩，所以乘以一个ratio
            p1.drawPoint(int(pos_tmp[0] * self.ratio * self.ori_scale), int(pos_tmp[1] * self.ratio * self.ori_scale))
            p1.setPen(QColor(0, 0, 255))
            p1.drawText(QPoint(int(pos_tmp[0] * self.ratio * self.ori_scale), int(pos_tmp[1] * self.ratio * self.ori_scale)), str(i))
            i += 1
        i = 1
        for pos_tmp in self.pos_xy_2:
            p1.setPen(QPen(QColor(255, 0, 255),
                           5 * self.ratio * self.ori_scale_2))  # 设置一个画笔，【5*self.ratio】代表半径，因为要考虑到标注的点的大小也要随着图片的放缩而放缩，所以乘以一个ratio
            # 用画笔再画布上绘制圆点。pos_xy中的点的位置是逻辑正确的位置，但是绘制的时候，要画一个物理正确的位置，即需要跟随图片放缩。关键点加入到pos_xy时接连除了ratio和ori_scale，这里要接连乘上
            p1.drawPoint(int(pos_tmp[0] * self.ratio * self.ori_scale_2 + self.layout_width + self.offset),
                         int(pos_tmp[1] * self.ratio * self.ori_scale_2))
            p1.setPen(QColor(0, 0, 255))
            p1.drawText(QPoint(int(pos_tmp[0] * self.ratio * self.ori_scale_2 + self.layout_width + self.offset),
                         int(pos_tmp[1] * self.ratio * self.ori_scale_2)), str(i))
            i += 1
        p1.end()

        # 绘制预览所用的半透明框
        if self.preview_flag:  # 确认是否需要开启预览（在鼠标点击右侧坐标点的时候，preview_flag会被设置为True）
            # 重新实例化
            p2 = QPainter()
            p2.begin(self)

            p2.setBrush(QBrush(QColor(0, 128, 128, 200), 1))  # QColor里前三位是rgb值，第四位是透明度，越小越透明
            indexs = [x.row() for x in self.listWidget.selectedIndexes()]
            for idx in indexs:
                # x和y也需要“逻辑位置错误，物理位置正确”。w和h代表框的边长，同样需要跟随图片的放缩而放缩
                x = int((self.pos_xy[idx][0] - 15) * self.ratio * self.ori_scale)
                y = int((self.pos_xy[idx][1] - 15) * self.ratio * self.ori_scale)
                w = int(30 * self.ratio * self.ori_scale)
                h = w
                p2.drawRect(x, y, w, h)  # 绘制方框
            p2.end()
            self.preview_flag = False  # 及时关闭预览模式

        if self.preview_flag_2:  # 确认是否需要开启预览（在鼠标点击右侧坐标点的时候，preview_flag会被设置为True）
            # 重新实例化
            p2_2 = QPainter()
            p2_2.begin(self)

            p2_2.setBrush(QBrush(QColor(0, 128, 128, 200), 1))  # QColor里前三位是rgb值，第四位是透明度，越小越透明
            indexs = [x.row() for x in self.listWidget_2.selectedIndexes()]
            for idx in indexs:
                # x和y也需要“逻辑位置错误，物理位置正确”。w和h代表框的边长，同样需要跟随图片的放缩而放缩
                x = int((self.pos_xy_2[idx][0] - 15) * self.ratio * self.ori_scale_2 + self.layout_width + self.offset)
                y = int((self.pos_xy_2[idx][1] - 15) * self.ratio * self.ori_scale_2)
                w = int(30 * self.ratio * self.ori_scale_2)
                h = w
                p2_2.drawRect(x, y, w, h)  # 绘制方框
            p2_2.end()
            self.preview_flag_2 = False  # 及时关闭预览模式

    # 切换上一张
    def prevImage(self, event=None):
        success = self.Save()  # 保存当前图片
        # 设置success标志是防止界面刚打开，还没有导入图片就点击这个按钮，没有办法保存当前图片更没有办法加载上一张图片，所以需要一个需要鲁棒性处理
        if success:
            if self.cur > 0:
                self.cur -= 1  # 游标向左移动
                self.Load()  # 加载上一张图片
            else:
                QMessageBox.information(self, "Tips", "TThe current is the first picture!", QMessageBox.Yes)
                return

    # 切换下一张    
    def nextImage(self, event=None):
        success = self.Save()
        if success:
            if self.cur < self.total - 1:
                self.cur += 1
                self.Load()
            else:
                QMessageBox.information(self, "Tips", "The current is the last picture!", QMessageBox.Yes)
                return

    # 保存动作
    def Save(self):
        if self.imageDir == '':
            QMessageBox.information(self, "Tips", "Please select an input IR folder", QMessageBox.Yes)
            return False
        if self.imageDir_2 == '':
            QMessageBox.information(self, "Tips", "Please select an input RGB folder", QMessageBox.Yes)
            return False
        if self.outDir == '':
            QMessageBox.information(self, "Tips", "Please select an output folder", QMessageBox.Yes)
            return False
        if len(self.pos_xy) != len(self.pos_xy_2):
            QMessageBox.information(self, "Tips", "IR points and RGB points not match", QMessageBox.Yes)
            return False
        # 分格式保存
        if self.label_format == 'mat':
            if len(self.pos_xy) > 0:
                sio.savemat(self.labelpath, {'IRPoints': self.pos_xy, 'RGBPoints': self.pos_xy_2, 'num': len(self.pos_xy)})
        elif self.label_format == 'h5':
            h5 = h5py.File(self.labelpath, 'w')
            h5['IRPoints'] = self.pos_xy
            h5['RGBPoints'] = self.pos_xy_2
            h5['num'] = len(self.pos_xy)
        elif self.label_format == 'txt':
            txt = open(self.labelpath, "w")
            for (point_1, point_2) in zip(self.pos_xy, self.pos_xy_2):
                txt.write(str(point_1[0]) + ',' + str(point_1[1]) + ',' + str(point_2[0]) + ',' + str(point_2[1]) + '\n')

                # json的比较复杂
        elif self.label_format == 'json':
            # 获取图片的base64编码
            pic = open(self.imagepath, 'rb')  # 以二进制读取图片
            data = pic.read()
            encodestr = base64.b64encode(data)  # 得到 byte 编码的数据
            encodestr = str(encodestr, 'utf-8')

            # 与labelme输出得标签格式完全一致
            Dict = {}
            Dict['version'] = '4.5.7'
            Dict['flags'] = {}
            Dict['shapes_IR'] = []
            Dict['shapes_RGB'] = []
            Dict['imagePath'] = self.imagepath
            Dict['imageData'] = encodestr
            Dict['imageHeight'] = int(self.img.height() / self.ori_scale)
            Dict['imageWidth'] = int(self.img.width() / self.ori_scale)
            for (xy, xy2) in zip(self.pos_xy, self.pos_xy_2):
                Dict['shapes_IR'].append({
                    'label': 'annPoints',
                    'points': [xy],
                    'group_id': None,
                    'shape_type': 'point',
                    'flags': {}
                })
                Dict['shapes_RGB'].append({
                    'label': 'annPoints',
                    'points': [xy2],
                    'group_id': None,
                    'shape_type': 'point',
                    'flags': {}
                })
            f = open(self.labelpath, 'w')
            json.dump(Dict, f, indent=2)  # 加上indent属性，json中的内容就会自动分行并且每行智能缩进。如果不加，所有的信息都会堆在一行，可读性很差
        print('第 %d 张图片已保存' % (self.cur + 1))
        return True

    # 根据索引跳转
    def gotoImage(self):
        idx = self.jump.text()  # 获取输入的索引值
        if idx == '':
            QMessageBox.information(self, "Tips", "Value cannot be empty", QMessageBox.Yes)
            self.jump.clear()
            return
        idx = int(idx)
        if 1 <= idx and idx <= self.total:
            success = self.Save()
            if success:
                self.cur = idx - 1
                self.Load()
        else:
            QMessageBox.information(self, "Tips", "Invalid index value", QMessageBox.Yes)
            self.jump.clear()
            return

    # 开启预览
    def Preview(self, item):
        self.preview_flag = True  # 鼠标已放置在了右侧坐标点上，开启预览信号
        self.update()  # 只开启预览信号不行，还要紧接着更新当前界面

    def Preview_2(self, item):
        self.preview_flag_2 = True  # 鼠标已放置在了右侧坐标点上，开启预览信号
        self.update()

    def detect_corners(self):
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        img = cv2.imread(self.imagepath_2)
        # gray = img
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, (self.checkboard_row, self.checkboard_column), None)
        if ret == True:
            self.listWidget_2.clear()
            # indexs = [x.row() for x in self.listWidget_2.selectedIndexes()]  # 获取选中的多个坐标点的下标
            # indexs.sort()  # 这个排序很关键，否则下面的【indexs[i]-i】也无法完成任务
            # if len(indexs) > 0:
            #     for i in range(len(indexs)):
            #         self.pos_xy_2.pop(indexs[
            #                               i] - i)  # indexs[i]-i 是核心，因为pop动作完成后，后面的元素会紧跟过来，这样的话下一个要删除的下标就不准确了，及时的减去当前的i，就可以解决这个问题。这个需要理解一下
            #         self.listWidget_2.takeItem(indexs[i] - i)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            corners2 = np.squeeze(corners2, axis=1)
            self.pos_xy_2 = corners2.tolist()
            for (x, y) in self.pos_xy_2:
                self.listWidget_2.insertItem(len(self.listWidget_2),
                                             '(' + str(round(x, 2)) + ',' + str(round(y, 2)) + ')')
        # self.img_resize()
        self.update()


    # 批量删除
    def Delete(self):
        indexs = [x.row() for x in self.listWidget.selectedIndexes()]  # 获取选中的多个坐标点的下标
        indexs.sort()  # 这个排序很关键，否则下面的【indexs[i]-i】也无法完成任务
        if len(indexs) > 0:
            for i in range(len(indexs)):
                self.pos_xy.pop(indexs[
                                    i] - i)  # indexs[i]-i 是核心，因为pop动作完成后，后面的元素会紧跟过来，这样的话下一个要删除的下标就不准确了，及时的减去当前的i，就可以解决这个问题。这个需要理解一下
                self.listWidget.takeItem(indexs[i] - i)
            self.update()  # 删除完后及时更新界面

    def Delete_2(self):
        indexs = [x.row() for x in self.listWidget_2.selectedIndexes()]  # 获取选中的多个坐标点的下标
        indexs.sort()  # 这个排序很关键，否则下面的【indexs[i]-i】也无法完成任务
        if len(indexs) > 0:
            for i in range(len(indexs)):
                self.pos_xy_2.pop(indexs[
                                      i] - i)  # indexs[i]-i 是核心，因为pop动作完成后，后面的元素会紧跟过来，这样的话下一个要删除的下标就不准确了，及时的减去当前的i，就可以解决这个问题。这个需要理解一下
                self.listWidget_2.takeItem(indexs[i] - i)
            self.update()  # 删除完后及时更新界面

    # 键盘点击事件
    def keyPressEvent(self, event):
        # 监听Esc键。尺寸复原，复原到刚被加载进来的尺寸，不是图片本来的尺寸。想要得到本来的尺寸还要再除以一个ori_scale
        if event.key() == Qt.Key_Escape:
            # 用到了之前的备份self.img
            self.scaled_img = self.img
            self.img_width = self.img.width()
            self.img_height = self.img.height()
            self.ratio = 1  # 只有鼠标滚轮才会使ratio发生改变，现在恢复到“原”尺寸了，ratio必要要重置为1
            self.update()

        # 监听Delete键
        if event.key() == Qt.Key_Delete:
            self.Delete()
            self.Delete_2()
        # 监听D键
        if event.key() == Qt.Key_D:
            self.nextImage()
        # 监听A键
        if event.key() == Qt.Key_A:
            self.prevImage()
        # 监听S键
        if event.key() == Qt.Key_S:
            success = self.Save()

        # 监听Ctrl+Z键   https://www.pythonf.cn/read/93347
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z:
            if len(self.pos_xy) > 1:
                self.pos_xy.pop()  # 后端弹出最后一个被加入的点
                self.listWidget.takeItem(len(self.pos_xy))  # 前台删除最后一个被加入的点
                self.update()

    # 鼠标点击时间
    def mousePressEvent(self, event):
        if self.img == None:
            return
        if event.button() == Qt.LeftButton:  # 鼠标左键按下
            if 0 < event.x() < self.img_width and 0 < event.y() < self.img_height:  # 因为图片被放缩了，如果点击到图片之外的区域，不去处理
                # 要旺后台pos_xy和前端listWidget传输逻辑位置正确的点，因为这些位置是要拿去保存到标签文件的。至于怎样在图片上绘制，就再连续乘以ratio和ori_scale
                self.listWidget.insertItem(len(self.listWidget),
                                           '(' + str(round(event.x() / self.ratio / self.ori_scale, 2)) + ',' + str(
                                               round(event.y() / self.ratio / self.ori_scale, 2)) + ')')
                self.pos_xy.append((event.x() / self.ratio / self.ori_scale, event.y() / self.ratio / self.ori_scale))
                self.update()
            if self.layout_width + self.offset < event.x() < self.layout_width + self.offset + self.img_width and 0 < event.y() < self.img_height:  # 因为图片被放缩了，如果点击到图片之外的区域，不去处理
                # 要旺后台pos_xy和前端listWidget传输逻辑位置正确的点，因为这些位置是要拿去保存到标签文件的。至于怎样在图片上绘制，就再连续乘以ratio和ori_scale
                self.listWidget_2.insertItem(len(self.listWidget_2), '(' + str(
                    round((event.x() - self.layout_width - self.offset) / self.ratio / self.ori_scale_2, 2)) + ',' + str(
                    round(event.y() / self.ratio / self.ori_scale_2, 2)) + ')')
                self.pos_xy_2.append(((event.x() - self.layout_width - self.offset) / self.ratio / self.ori_scale_2,
                                      event.y() / self.ratio / self.ori_scale_2))
                self.update()
            # else:
            #     QMessageBox.information(self,"Tips","Invalid label position",QMessageBox.Yes)

    # 鼠标移动事件
    def mouseMoveEvent(self, event):
        if self.img == None:
            return
        new_x = event.x()
        new_y = event.y()
        if new_x <= self.img.width() and new_y <= self.img.height():
            text = 'x:' + str(round(new_x / self.ratio / self.ori_scale, 2)) + '    |    y:' + str(round(new_y / self.ratio / self.ori_scale, 2))
            self.location.setAlignment(Qt.AlignCenter)
            # self.location.setFont(QFont("微软雅黑",10))
            self.location.setText("<font color=%s>%s</font>" % ('#8968CD', text))
        elif self.layout_width + self.offset < new_x < self.layout_width + self.offset + self.img_width and 0 < new_y < self.img_height:
            text = ('x:' + str(round((new_x - self.layout_width - self.offset) / self.ratio / self.ori_scale_2, 4)) +
                    '    |    y:' + str(round((new_y - self.layout_height - self.offset) / self.ratio / self.ori_scale_2, 4)))
            self.location.setAlignment(Qt.AlignCenter)
            # self.location.setFont(QFont("微软雅黑",10))
            self.location.setText("<font color=%s>%s</font>" % ('#8968CD', text))
        else:
            self.location.setAlignment(Qt.AlignCenter)
            # self.location.setFont(QFont("微软雅黑",10))
            self.location.setText("<font color=%s>%s</font>" % ('#8968CD', '--    |   --'))

    # 鼠标滚动
    # def wheelEvent(self, event):
    #     self.preview_flag = True
    #     self.preview_flag_2 = True
    #     if event.angleDelta().y() < 0:  # 下滚,缩小
    #         if self.img_width > 25 and self.img_height > 25:
    #             new_weight = self.img_width - 25 * self.x_y_scale
    #             new_height = self.img_height - 25
    #             self.ratio = new_weight / self.img.width()  # 只有滚轮滑动才会更新ratio
    #             self.img_width = new_weight
    #             self.img_height = new_height
    #             self.scaled_img = self.img.scaled(self.img_width, self.img_height)
    #
    #             self.repaint()
    #     elif event.angleDelta().y() > 0:  # 上滚,放大
    #         new_weight = self.img_width + 25 * self.x_y_scale
    #         new_height = self.img_height + 25
    #         self.ratio = new_weight / self.img.width()
    #         self.img_width = new_weight
    #         self.img_height = new_height
    #         self.scaled_img = self.img.scaled(self.img_width, self.img_height)
    #         self.repaint()


    def click_input_dir(self):
        self.click_imageDir = QFileDialog.getExistingDirectory(self, 'Please select a folder for IR', './')
        # 判空
        if self.click_imageDir == '':
            QMessageBox.information(self, "Tips", "Please select a folder", QMessageBox.Yes)
            return
        if self.click_imageDir != "":
            self.imageDir = self.click_imageDir
        # 判断该目录下有没有图片
        self.imageList = os.listdir(self.imageDir)
        self.imageList = [f for f in self.imageList if f.endswith(('.JPG', '.png', 'bmp', 'jpeg'))]  # 得到文件夹下指定后缀的所有文件路径

        if len(self.imageList) == 0:
            QMessageBox.information(self, "Tips", "There are no picture files in this directory", QMessageBox.Yes)
            return

        self.imageList.sort()  # 让图片粗略的按顺序导入
        self.cur = 0  # 遍历图片的游标
        self.total = len(self.imageList)  # 图片总数

    def click_input_dir_2(self):

        self.click_imageDir_2 = QFileDialog.getExistingDirectory(self, 'Please select a folder for RGB', './')
        # 判空
        if self.click_imageDir_2 == '':
            QMessageBox.information(self, "Tips", "Please select a folder for RGB", QMessageBox.Yes)
            return

        if self.click_imageDir_2 != "":
            self.imageDir_2 = self.click_imageDir_2

        # 判断该目录下有没有图片
        self.imageList_2 = os.listdir(self.imageDir_2)
        self.imageList_2 = [f for f in self.imageList_2 if
                            f.endswith(('.JPG', '.png', 'bmp', 'jpeg'))]  # 得到文件夹下指定后缀的所有文件路径

        if len(self.imageList_2) == 0:
            QMessageBox.information(self, "Tips", "There are no picture files in this directory", QMessageBox.Yes)
            return

        self.imageList_2.sort()  # 让图片粗略的按顺序导入
        self.cur_2 = 0  # 遍历图片的游标
        self.total_2 = len(self.imageList_2)

        if len(self.imageList_2) != len(self.imageList):
            QMessageBox.information(self, "Tips", "Number of Visual images not match IR images", QMessageBox.Yes)
            return

    # 打开输入目录
    def click_output_dir(self):
        self.click_outDir = QFileDialog.getExistingDirectory(self, 'Please select a folder for output', './')

        # 判空
        if self.click_outDir == '':
            QMessageBox.information(self, "Tips", "Please select a folder for output", QMessageBox.Yes)
            return
        if self.click_outDir != "":
            self.outDir = self.click_outDir

        # 输入和输出目录都有了，直接开始导入图片和标签
        if self.imageDir != '' and self.imageDir_2 != '':
            self.Load()
        else:
            QMessageBox.information(self, "Tips", "Please select a folder for output", QMessageBox.Yes)
            return
    
    @staticmethod
    def find_resize(img_width, img_height, layout_width, layout_height):

        if img_width < layout_width and img_height < layout_height:
            x_ = (layout_width) / img_width
            y_ = (layout_height) / img_height
            if x_ > y_:
                ori_scale = (layout_height) / img_height
                img_width = int(img_width * ori_scale)
                img_height = layout_height
            else:
                ori_scale = (layout_width) / img_width
                img_width = layout_width
                img_height = int(img_height * ori_scale)
        
        elif img_width < layout_width and img_height >= layout_height:
            ori_scale = (layout_height) / img_height
            img_width = int(img_width * ori_scale)
            img_height = layout_height
        
        
        elif img_width >= layout_width and img_height < layout_height:
            ori_scale = (layout_width) / img_width
            img_width = layout_width
            img_height = int(img_height * ori_scale)
        else:
            x_ = img_width / (layout_width)
            y_ = img_height / (layout_height)
            # 寻找一个越界范围更大的
            if x_ < y_:
                ori_scale = (layout_height) / img_height
                img_width = int(img_width * ori_scale)
                img_height = layout_height
            else:
                ori_scale = (layout_width) / img_width
                img_width = layout_width
                img_height = int(img_height * ori_scale)
        x_y_scale = img_width / img_height
        return img_width, img_height, ori_scale, x_y_scale


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # w = MyMainForm(imageDir=r'D:\OneDrive-Sudao\dataset\HKUST-Multimodal-feature-matching',
    #                imageDir_2=r'D:\OneDrive-Sudao\dataset\HKUST-Multimodal-feature-matching',
    #                outDir=r'D:\OneDrive-Sudao\dataset\HKUST-Multimodal-feature-matching')
    w = MyMainForm(imageDir=r'E:\Dataset\Defect-segmentation',
                   imageDir_2=r'E:\Dataset\Defect-segmentation',
                   outDir=r'E:\Dataset\Defect-segmentation')
    # imageDir - IR, imageDir_2 - VIS
    # w.showFullScreen() # 设置全屏
    w.show()
    sys.exit(app.exec_())
