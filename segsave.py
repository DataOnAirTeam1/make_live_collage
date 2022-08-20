import cv2
import numpy as np
import tensorflow as tf

IMAGE_SIZE = 512

def makeWhiteEdge(img_arr, save_path=None, k_size=3, iterations=3):
    im_alpha = img_arr[:,:,3]
    kernel = np.ones((k_size,k_size), np.uint8)
    result = cv2.dilate(im_alpha, kernel, iterations=iterations)

    white_space_mask = np.stack([np.where(result - im_alpha>0, True,False)]*3, axis=2)

    img_arr[:,:,3] = result
    img_arr[:,:,:3][white_space_mask] = 255
    img_arr = np.stack([img_arr[:,:,2], img_arr[:,:,1], img_arr[:,:,0], img_arr[:,:,3]], axis=2)
    if save_path:
        cv2.imwrite(save_path, img_arr)
    return img_arr

def read_image(image_path, original=False):
    image = tf.io.read_file(image_path)
    image = tf.image.decode_png(image, channels=3)
    image.set_shape([None, None, 3])
    if not original:
        image = tf.image.resize(images=image, size=[IMAGE_SIZE, IMAGE_SIZE])
        image = image/255
    return image

def segSave(model, image_path, save_path=None):
    original_image = read_image(image_path, original=True)
    input_image = read_image(image_path)
    input_pred = model.predict(input_image[np.newaxis,...])

    thresh_hold = 0.3
    pred_mask = input_pred > thresh_hold
    alpha = cv2.resize(np.squeeze(np.where(pred_mask, 1.0,0)), (original_image.shape[1], original_image.shape[0]))
    alpha = np.where(alpha>0,1,0).astype(np.float32)

    try:
        contours_coor ,info = cv2.findContours(alpha.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        info_ = np.where(info[0][:,-1]==-1)[0]
        for i, num in enumerate(info_):
            contour_coor = contours_coor[num]
            if i == 0:
                filled_hole = cv2.fillConvexPoly(alpha.astype(np.uint8), np.squeeze(contour_coor), 255)
            else :
                filled_hole = cv2.fillConvexPoly(filled_hole, np.squeeze(contour_coor), 255)
        filed_mask = np.where(filled_hole[...,np.newaxis] > 0, 1,0)
        masked_image = original_image * filed_mask
        masked_image_png = np.concatenate([masked_image[:,:,2][...,np.newaxis], masked_image[:,:,1][...,np.newaxis],
                          masked_image[:,:,0][...,np.newaxis] ,(filed_mask).astype(np.uint8)*255], axis=2)
    except:
        alpha_ = alpha[...,np.newaxis]
        masked_image = original_image * alpha_
        masked_image_png = np.concatenate([masked_image[:,:,2][...,np.newaxis], masked_image[:,:,1][...,np.newaxis],
                                           masked_image[:,:,0][...,np.newaxis], (alpha_).astype(np.uint8)*255 ], axis=2)
    if save_path:
        cv2.imwrite(save_path, masked_image_png)

    return masked_image_png