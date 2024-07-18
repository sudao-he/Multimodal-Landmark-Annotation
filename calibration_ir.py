import numpy as np
import cv2
import glob
import matplotlib as mpl
import matplotlib.pyplot as plt
import os
from scipy.io import loadmat





verbose = False
calibrate = True
distort = True

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
CHECKERBOARD = (11, 8)
# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((1, CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[0, :, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
square_size = (35, 35)
objp[0, :, 0] *= square_size[0]
objp[0, :, 1] *= square_size[1]
# print(objp)

# Arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.
thre_ratio = 0.6
sobel_threshold = 40

landmark_path = (r'E:\fasade_project\20240529CameraCalibration\Output')
check_path = (r'E:\fasade_project\20240529CameraCalibration\check')
IR_path = r'E:\fasade_project\20240529CameraCalibration\thermo'
images = glob.glob(r'{}\*.jpg'.format(IR_path))

for fname in images:
    # img = np.fromfile(fname, dtype='float32').reshape((512, 640))
    # gray_img = (img - img.min()) / (img.max() - img.min()) * 255
    # gray_img = gray_img.astype(np.uint8)
    # color_map = cv2.applyColorMap(gray_img, cv2.COLORMAP_JET)
    color_map = cv2.imread(fname)
    gray_img = cv2.cvtColor(color_map, cv2.COLOR_BGR2GRAY)

    filepath, fullname = os.path.split(fname)
    fname_woext, ext = os.path.splitext(fullname)
    # print('shape:', gray_img.shape[::-1])


    try:
        ROWS = 11
        COLOMONS = 8
        mat = loadmat('{}/{}.mat'.format(landmark_path, fname_woext))
        corners = mat['IRPoints']
        corners = np.expand_dims(corners, axis=1).astype(np.float32)

        corners_pixel = corners.copy()
        corners_pixel = cv2.cornerSubPix(gray_img, corners_pixel, (6, 6), (-1, -1), criteria)
        color_map = cv2.drawChessboardCorners(color_map, (ROWS, COLOMONS), corners_pixel, True)
        if verbose:
            for i in range(corners_pixel.shape[0]):
                text = str(i + 1)
                cv2.putText(color_map, text, (int(corners[i, 0, 0]), int(corners[i, 0, 1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.imwrite('{}/log-{}.jpg'.format(check_path, fname_woext), color_map)
            cv2.imshow('img', color_map)
            cv2.waitKey(0)
        objpoints.append(objp)
        imgpoints.append(corners_pixel)
    except FileNotFoundError:
        pass


# cv2.destroyAllWindows()
if calibrate:
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray_img.shape[::-1], None, None)
    # h, w = color_map.shape[:2]
    # newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
    np.savetxt("ir_inner.txt", mtx)
    np.savetxt("ir_distort.txt", dist)

    print("Saved inner.txt")
    print("Saved distort.txt")

# mean_error = []
# for i in range(len(objpoints)):
#     imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
#     error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2)/len(imgpoints2)
#     mean_error.append(error)
# mean_error = np.array(mean_error)
# q1 = np.percentile(mean_error, 25)
# q2 = np.percentile(mean_error, 50)
# q3 = np.percentile(mean_error, 75)
# #
# plt.figure(figsize=(8, 6))
# plt.boxplot(mean_error, labels=['Distortion error'])
# plt.xlabel('')
# plt.ylabel('Error')
# plt.grid(False)
# plt.show()
# print('Max: {:.4f}, Min: {:.4f}, Q1:{:.4f}, Q3:{:.4f}, Q2:{:.4f}'.format(mean_error.max(), mean_error.min(), q1, q3, q2))
if distort:
    for fname in images:
        # img = np.fromfile(fname, dtype='float32').reshape((512, 640))
        img = cv2.imread(fname)
        h, w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
        # undistort
        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        filepath, fullname = os.path.split(fname)
        fname_woext, ext = os.path.splitext(fullname)
        # crop the image
        x, y, w, h = roi

        dst = dst[y:y + h, x:x + w]
        cv2.imwrite('{}/undist-{}.png'.format(check_path, fname_woext), dst)
        # plt.figure(0)
        # vnorm = mpl.colors.Normalize(vmin=dst.min(), vmax=dst.max())
        # plt.imshow(dst, cmap=mpl.colormaps['rainbow'], norm=vnorm)
        # plt.axis('off')
        # plt.colorbar()
        # plt.savefig('{}/undist-{}.png'.format(check_path, fname_woext), bbox_inches='tight', pad_inches=0.0)
        # plt.close(0)
        # print("Undistorting...", (i + 1).__str__() + "/" + images.__len__().__str__())
