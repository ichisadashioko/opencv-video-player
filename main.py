import os
import argparse
import time
import cv2
import sys

# create a video player with opencv frame by frame

parser = argparse.ArgumentParser()

parser.add_argument('infile', type=str, help="Path to video file")
args = parser.parse_args()

print('args', args)

if not os.path.exists(args.infile):
    raise IOError('File not found')

video_capture = cv2.VideoCapture(args.infile)
if not video_capture.isOpened():
    print("Could not open video")

    video_capture.release()
    cv2.destroyAllWindows()
    sys.exit(1)

number_of_frames = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
current_frame_index = 0
pausing = False
needed_update = False


def set_frame(index):
    global current_frame_index, needed_update

    if index != current_frame_index:
        current_frame_index = index
        needed_update = True
        current_frame_index = current_frame_index % number_of_frames


# add a slider for scrolling through the video
class Slider(object):
    """Slider class for video player"""

    def __init__(self, name, max):
        self.name = name
        self.max = max
        self.value = 0

    def update(self, value):
        self.value = value

    def get_value(self):
        return self.value


# add the slider to the cv2 window
slider = Slider("frame", number_of_frames - 1)
cv2.createTrackbar('frame', 'Video', 0, number_of_frames - 1, lambda x: set_frame(x))
cv2.setTrackbarPos('frame', 'Video', 0)
slider_bar = cv2.getTrackbarPos('frame', 'Video')
slider_bar_toggle = (slider_bar != 0)  # only update the slider bar when it is pressed
print("slider_bar_toggle", slider_bar_toggle)
print("slider_bar", slider_bar)
# show the video with the slider bar
while True:
    ret, frame = video_capture.read()
    if not ret:
        break
    # did the user select a slider bar?
    # how do we detect that the trackbar has been selected?

    slider_bar_toggle = cv2.getTrackbarPos('frame', 'Video') != 0
    if slider_bar_toggle:
        slider.update(slider_bar)
        needed_update = True
    if needed_update:
        slider.set()
        needed_update = False
    cv2.imshow('Video', frame)
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break
    slider_bar_toggle = False
    # if the user wants to pause, we must increase the value of a frame
    if k == 32:
        pausing = True
        while pausing:
            time.sleep(1)
            slider.update(slider_bar)
            if not cv2.getTrackbarPos('frame', 'Video') != 0:
                break
    pausing = False
cv2.destroyAllWindows()
video_capture.release()
sys.exit()


# start the main loop where we get all the frames from the video capture

last_frame = None
while True:
    if pausing:
        if last_frame is None:
            video_capture.set(cv2.cv2.CAP_PROP_POS_FRAMES, current_frame_index)
            ret, frame = video_capture.read()
            if ret is False:
                print("continue failed")
                break
            last_frame = frame

        cv2.imshow('Video', last_frame)
    else:
        # get the next frame
        ret, frame = video_capture.read()
        print(ret, frame.shape)
        # convert the frame to RGB since opencv uses BGR and we need RGB
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # show the frame in the video player
        last_frame = frame
        cv2.imshow('Video', frame)

    # check for the escape key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release the video capture and close the windows
video_capture.release()
cv2.destroyAllWindows()
sys.exit(1)
