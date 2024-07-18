import numpy as np
import cv2
import glob
import os
from scipy.io import loadmat


def find_vis_name(ir_name, vis_dir):
    number_loc = ir_name.find('_')
    number_index = int(ir_name[number_loc + 1:number_loc + 5])
    vis_name = 'DJI_{:04d}_W.JPG'.format(number_index - 1)
    vis_path = vis_dir + vis_name
    return vis_path


def checkboard(im1, im2, d=100):
    im1 = im1 * 1.0
    im2 = im2 * 1.0
    mask = np.zeros_like(im1)
    for i in range(mask.shape[0] // d + 1):
        for j in range(mask.shape[1] // d + 1):
            if (i + j) % 2 == 0:
                mask[i * d:(i + 1) * d, j * d:(j + 1) * d, :] += 1
    return im1 * mask + im2 * (1 - mask)



# Set the path to the images captured by the left and right cameras


print("Extracting image coordinates of respective 3D pattern ....\n")

# Termination criteria for refining the detected corners
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
ROWS = 11
COLUMNS = 8

objp = np.zeros((11 * 8, 3), np.float32)
objp[:, :2] = np.mgrid[0:11, 0:8].T.reshape(-1, 2)

img_ptsL = np.empty((0, 1, 2))
img_ptsR = np.empty((0, 1, 2))
obj_pts = np.empty((0, 3))


vis_dir = r'E:\fasade_project\20240529CameraCalibration\vis\\'
landmark_path = (r'E:\fasade_project\20240529CameraCalibration\Output\\')
check_path = (r'E:\fasade_project\20240529CameraCalibration\check\\')
IR_path = r'E:\fasade_project\20240529CameraCalibration\thermo\\'
mats = glob.glob('{}/*.mat'.format(landmark_path))

new_mtxL = np.loadtxt('ir_inner.txt', dtype=np.float64)
distL = np.loadtxt('ir_distort.txt', dtype=np.float64)
# new_mtxR = np.loadtxt('vis_inner_stereo.txt', dtype=np.float64)
# distR = np.loadtxt('vis_distort_stereo.txt', dtype=np.float64)
for fname in mats:
    mat = loadmat(fname)
    corners = mat['IRPoints']
    corners = np.expand_dims(corners, axis=1).astype(np.float32)
    filepath, fullname = os.path.split(fname)
    fname_woext, ext = os.path.splitext(fullname)

    # imgL = np.fromfile('{}/{}.raw'.format(IR_path, fname_woext), dtype='float32').reshape((512, 640))
    # grayL = (imgL - imgL.min()) / (imgL.max() - imgL.min()) * 255
    # grayL = grayL.astype(np.uint8)
    # colorL = cv2.applyColorMap(grayL, cv2.COLORMAP_JET)
    imgL = cv2.imread('{}/{}.JPG'.format(IR_path, fname_woext))
    colorL = imgL
    grayL = cv2.cvtColor(colorL, cv2.COLOR_BGR2GRAY)

    cornersL = corners.copy()
    cornersL = cv2.cornerSubPix(grayL, cornersL, (6, 6), (-1, -1), criteria)

    img_name = find_vis_name(fname_woext, vis_dir)
    imgR = cv2.imread(img_name)
    grayR = cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(grayR, (ROWS, COLUMNS), None)
    obj_pts = np.append(obj_pts, objp, axis=0)
    cornersR = cv2.cornerSubPix(grayR, corners, (11, 11), (-1, -1), criteria)
    img_ptsR = np.append(img_ptsR, cornersR, axis=0)
    img_ptsL = np.append(img_ptsL, cornersL, axis=0)

h, w = imgL.shape[:2]
newcameramtxL, roi = cv2.getOptimalNewCameraMatrix(new_mtxL, distL, (w, h), 1, (w, h))
img_ptsL_undist = cv2.undistortPoints(img_ptsL, new_mtxL, distL, None, newcameramtxL)
# img_ptsR_undist = cv2.undistortPoints(img_ptsR, new_mtxR, distR, None, new_mtxR)
img_ptsR_undist = img_ptsR
homography_ir2vis, _ = cv2.findHomography(img_ptsL_undist, img_ptsR_undist)
homography_vis2ir, _ = cv2.findHomography(img_ptsR_undist, img_ptsL_undist)
zero_array = np.ones((imgL.shape[0], imgL.shape[1]))
mask = 1 - cv2.warpPerspective(zero_array, homography_ir2vis, (imgR.shape[1], imgR.shape[0]))
maskIRinVis = np.expand_dims(mask, 2).repeat(3, axis=2)
keepIRinVis = np.expand_dims(1-mask, 2).repeat(3, axis=2)

"""
Save Parameters
"""
param = {'ir_intrinsics': new_mtxL, 'ir_distortion_coeffs': distL, 'ir2vis': homography_ir2vis, 'vis2ir': homography_vis2ir}
np.savez('cam_param.npz', **param)

imgs = glob.glob('{}/*.JPG'.format(IR_path))
for fname in imgs:
    # imgL = np.fromfile(fname, dtype='float32').reshape((512, 640))
    # grayL = (imgL - imgL.min()) / (imgL.max() - imgL.min()) * 255
    # grayL = grayL.astype(np.uint8)
    # colorL = cv2.applyColorMap(grayL, cv2.COLORMAP_JET)
    imgL = cv2.imread(fname)
    colorL = imgL
    grayL = cv2.cvtColor(colorL, cv2.COLOR_BGR2GRAY)


    filepath, fullname = os.path.split(fname)
    fname_woext, ext = os.path.splitext(fullname)
    img_name = find_vis_name(fname_woext, vis_dir)
    imgR = cv2.imread(img_name)
    dstL = cv2.undistort(colorL, new_mtxL, distL, None, newcameramtxL)
    # dstR = cv2.undistort(imgR, new_mtxR, distR, None, new_mtxR)
    dstR = imgR
    # ir_warp = cv2.warpPerspective(dstL, homography_ir2vis, (imgR.shape[1], imgR.shape[0]))
    # ir_in_vis = ir_warp + dstR * maskIRinVis
    # cv2.imwrite('{}/warp-{}.png'.format(check_path, fname_woext), ir_in_vis)



    vis_warp = cv2.warpPerspective(dstR, homography_vis2ir, (imgL.shape[1], imgL.shape[0]))
    imgcat_out = checkboard(dstL, vis_warp)
    cv2.imwrite('{}/imgCat-{}.png'.format(check_path, fname_woext), imgcat_out)

    # grayR = cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY)
    # ret, corners = cv2.findChessboardCorners(grayR, (ROWS, COLUMNS), None)
    # cornersR = cv2.cornerSubPix(grayR, corners, (11, 11), (-1, -1), criteria)
    # imgR = cv2.drawChessboardCorners(imgR, (11, 8), cornersR, True)
    # for i in range(cornersR.shape[0]):
    #     text = str(i + 1)
    #     cv2.putText(imgR, text, (int(corners[i, 0, 0]), int(corners[i, 0, 1])), cv2.FONT_HERSHEY_SIMPLEX, 25,
    #                 (255, 255, 255), 1)
    # cv2.imwrite('{}/img-{}.jpg'.format(check_path, fname_woext), imgR)