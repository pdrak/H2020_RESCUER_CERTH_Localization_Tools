import cv2

#cap = cv2.VideoCapture(2)
cap = cv2.VideoCapture('udp://127.0.0.1:8555?overrun_nonfatal=1&fifo_size=500000')

num = 0

while cap.isOpened():

    succes, img = cap.read()

    img = cv2.resize(img, (640,360), interpolation = cv2.INTER_LANCZOS4)

    k = cv2.waitKey(5)

    if k == 27:
        break
    elif k == ord('s'): # wait for 's' key to save and exit
        cv2.imwrite('images/img' + str(num) + '.png', img)
        print("image saved!")
        num += 1

    cv2.imshow('Img',img)

# Release and destroy all windows before termination
cap.release()

cv2.destroyAllWindows()
