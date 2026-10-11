import cv2

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)
print("opened:", cap.isOpened())
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
ok, frame = cap.read()
print("read ok:", ok, ("shape=" + str(frame.shape)) if ok else "")
if ok:
    cv2.imwrite("/home/ethan/rknn_workspace/cam_test.jpg", frame)
    print("saved /home/ethan/rknn_workspace/cam_test.jpg")
cap.release()
