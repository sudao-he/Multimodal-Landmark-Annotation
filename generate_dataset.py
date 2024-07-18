
import numpy as np
import cv2
from tqdm import tqdm
import glob
import os
import scipy.io


def find_vis_name(ir_name, vis_dir):
    number_loc = ir_name.find('_')
    number_index = int(ir_name[number_loc + 1:number_loc + 5])
    vis_name = 'DJI_{:04d}_W.JPG'.format(number_index - 1)
    vis_path = vis_dir + vis_name
    return vis_path

def cat2images(limg, rimg):
    HEIGHT = limg.shape[0]
    WIDTH = limg.shape[1]
    imgcat = np.zeros((HEIGHT, WIDTH*2+20, 3))
    imgcat[:, :WIDTH, :] = limg
    imgcat[:, -WIDTH:, :] = rimg
    for i in range(int(HEIGHT / 32)):
        imgcat[i*32:i*32+2, :, :] = 255
    return imgcat


output = 'color' ### color 输出彩色IR图， gray输出灰度IR图
cam_param = np.load('cam_param.npz')
name = 'A1Sequence'
"""
param = {'ir_intrinsics': IR内参, 'ir_distortion_coeffs': IR畸变,
          'ir2vis': IR至RGB单应性矩阵, 'vis2ir': RGB至IR单应性矩阵}
"""
new_mtxL, distL = (cam_param['ir_intrinsics'], cam_param['ir_distortion_coeffs'])
homography_ir2vis, homography_vis2ir = cam_param['ir2vis'], cam_param['vis2ir']
vis_dir = 'E:/fasade_project/{}/test/VIS_register/'.format(name)
imgs = glob.glob('E:/fasade_project/{}//raw/*.raw'.format(name))

if not os.path.exists('E:/fasade_project/{}//test/VIS/'.format(name)):
    os.makedirs('E:/fasade_project/{}//test/VIS/'.format(name))
if not os.path.exists('E:/fasade_project/{}//test/IR/'.format(name)):
    os.makedirs('E:/fasade_project/{}//test/IR/'.format(name))
if not os.path.exists('E:/fasade_project/{}//test/IR-color/'.format(name)):
    os.makedirs('E:/fasade_project/{}//test/IR-color/'.format(name))
if not os.path.exists('E:/fasade_project/{}//test/tem_field/'.format(name)):
    os.makedirs('E:/fasade_project/{}//test/tem_field/'.format(name))


for fname in imgs:
    imgL = np.fromfile(fname, dtype='float32').reshape((512, 640))
    grayL = (imgL - imgL.min()) / (imgL.max() - imgL.min()) * 255
    grayL = grayL.astype(np.uint8)
    colorL = cv2.applyColorMap(grayL, cv2.COLORMAP_JET)
    filepath, fullname = os.path.split(fname)
    fname_woext, ext = os.path.splitext(fullname)
    img_name = find_vis_name(fname_woext, vis_dir)
    imgR = cv2.imread(img_name)
    dstL = cv2.undistort(imgL, new_mtxL, distL, None, new_mtxL)
    # scipy.io.savemat('E:/fasade_project/{}/test/tem_field/{}.mat'.format(name, fname_woext), mdict={'tem_field': dstL})
    dstL.tofile('E:/fasade_project/{}/test/tem_field/{}.raw'.format(name, fname_woext))
    gray_img = (dstL - np.min(dstL[dstL > 0])) / (np.max(dstL[dstL > 0]) - np.min(dstL[dstL > 0])) * 255
    gray_img = gray_img.astype(np.uint8)
    color_img = cv2.applyColorMap(gray_img, cv2.COLORMAP_JET)
    # dstR = cv2.undistort(imgR, new_mtxR, distR, None, new_mtxR)
    vis_warp = cv2.warpPerspective(imgR, homography_vis2ir, (imgL.shape[1], imgL.shape[0]))

    cv2.imwrite('E:/fasade_project/{}/test/IR-color/{}.png'.format(name, fname_woext),
                    color_img)
    cv2.imwrite('E:/fasade_project/{}/test/IR/{}.png'.format(name, fname_woext),
                    gray_img)
    cv2.imwrite('E:/fasade_project/{}/test/VIS/{}.png'.format(name, fname_woext), vis_warp)
