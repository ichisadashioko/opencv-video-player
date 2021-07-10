import os
import argparse
import time
import cv2
import sys
import threading


def parse_secs(secs: float):
    hours = 0
    mins = 0
    if secs >= 3600:
        hours = int(secs / 3600)
        secs = secs % 3600
    if secs >= 60:
        mins = int(secs / 60)
        secs = secs % 60

    return {
        'hours': hours,
        'mins': mins,
        'seconds': secs
    }

# create a video player with opencv frame by frame
# always use single quote ' instead of " for string


parser = argparse.ArgumentParser()

parser.add_argument('infile', type=str, help='Path to video file')
args = parser.parse_args()

print('args', args)

if not os.path.exists(args.infile):
    raise IOError('File not found')

video_capture = cv2.VideoCapture(args.infile)
if not video_capture.isOpened():
    print('Could not open video')

    video_capture.release()
    sys.exit(1)

NUMBER_OF_FRAMES = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
VIDEO_FPS = video_capture.get(cv2.CAP_PROP_FPS)
LOOP_WAIT_TIME_MS = int(1000 / VIDEO_FPS)
current_frame_index = 0
next_frame_index = 0
pausing = False
needed_update_after_slider_scrolled = False
# flag for indicating that the trackbar was set by code but not the user
slider_scrolled_by_code = False

# print video info
print('Video Info')
print('Number of frames:', NUMBER_OF_FRAMES)
print('Frames per second:', VIDEO_FPS)
print('Loop wait time:', LOOP_WAIT_TIME_MS)

WINDOW_NAME = 'video'
# give slider a name to use in the window
SLIDER_NAME = 'frame_index_slider'

# create the window before creating the trackbar
cv2.namedWindow(WINDOW_NAME)


def normalize_frame_index(index: int, max: int):
    index = index % max
    return index


# create a new thread that will update the flag after a timeout period. If the trackbar is updated during the timeout, the thread will not update the flag.
latest_thread_creation_time = 0
UPDATE_TRACKBAR_SEEKING_FLAG_MS = 50
UPDATE_TRACKBAR_SEEKING_FLAG_SECS = UPDATE_TRACKBAR_SEEKING_FLAG_MS / 1000


def update_thread_fn():
    global latest_thread_creation_time, needed_update_after_slider_scrolled
    created_time = time.perf_counter()
    latest_thread_creation_time = created_time
    time.sleep(UPDATE_TRACKBAR_SEEKING_FLAG_SECS)
    if created_time == latest_thread_creation_time:
        frame_index = int(cv2.getTrackbarPos(SLIDER_NAME, WINDOW_NAME))
        frame_index = normalize_frame_index(frame_index, NUMBER_OF_FRAMES)
        if frame_index == current_frame_index:
            return

        needed_update_after_slider_scrolled = True


def slider_scrolled(val):
    global needed_update_after_slider_scrolled, pausing, slider_scrolled_by_code

    if slider_scrolled_by_code:
        slider_scrolled_by_code = False
        return

    pausing = True
    threading.Thread(target=update_thread_fn, daemon=True).start()


cv2.createTrackbar(SLIDER_NAME, WINDOW_NAME, 0, int(NUMBER_OF_FRAMES - 1), slider_scrolled)


def update_trackbar_state(frame):
    global slider_scrolled_by_code
    slider_scrolled_by_code = True

    cv2.setTrackbarPos(SLIDER_NAME, WINDOW_NAME, frame)


last_frame = None
loop_counter = 0
while True:
    try:
        loop_counter += 1
        frame = None

        if needed_update_after_slider_scrolled:
            current_frame_index = int(cv2.getTrackbarPos(SLIDER_NAME, WINDOW_NAME))
            current_frame_index = normalize_frame_index(current_frame_index, NUMBER_OF_FRAMES)
            video_capture.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)
            # read the frame and store it in the last_frame
            ret, frame = video_capture.read(current_frame_index)

            if not ret:
                print('current_frame_index', current_frame_index)
                print('loop_counter:', loop_counter)
                print('video_capture.get(cv2.CAP_PROP_POS_FRAMES)', video_capture.get(cv2.CAP_PROP_POS_FRAMES))
                raise IOError('Failed to read frame!')

            last_frame = frame

            needed_update_after_slider_scrolled = False
            continue

        if not pausing:
            # stop reading if the final frame is reached
            next_frame_index = int(video_capture.get(cv2.CAP_PROP_POS_FRAMES))
            if next_frame_index < NUMBER_OF_FRAMES:
                ret, frame = video_capture.read()

                if not ret:
                    print('current_frame_index', current_frame_index)
                    print('loop_counter:', loop_counter)
                    print('video_capture.get(cv2.CAP_PROP_POS_FRAMES)', video_capture.get(cv2.CAP_PROP_POS_FRAMES))
                    raise IOError('Failed to read frame!')

                current_frame_index = next_frame_index
                last_frame = frame
            update_trackbar_state(current_frame_index)
        else:
            if last_frame is None:
                print('current_frame_index', current_frame_index)
                print('loop_counter:', loop_counter)
                print('video_capture.get(cv2.CAP_PROP_POS_FRAMES)', video_capture.get(cv2.CAP_PROP_POS_FRAMES))
                raise RuntimeError('Last frame is None, application state is unexpected')
            else:
                frame = last_frame

        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(LOOP_WAIT_TIME_MS) & 0xFF

        # handle keyboard events

        # if 'space' key is press, then pause the video
        if key == 32:
            pausing = not pausing
        # if 'q' or ESC key is pressed, exit
        elif key == 27 or key == ord('q'):
            break
        # if '+' or '>' key is pressed, increment the frame index and pause the video
        elif key == ord('+') or key == ord('<') or key == 83:
            # Next frame feature
            # If the video is paused, increase the frame by 1 and store the frame in the last_frame for displaying on the next iteration.
            # If the final frame is reached, do nothing.
            # If the video is playing, pause the video and display the next frame.
            # If the current frame is the final frame, only pause the video.

            next_frame_index = int(video_capture.get(cv2.CAP_PROP_POS_FRAMES))
            if next_frame_index < NUMBER_OF_FRAMES:
                current_frame_index = next_frame_index
                video_capture.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)
                ret, frame = video_capture.read()

                if not ret:
                    print('current_frame_index', current_frame_index)
                    print('loop_counter:', loop_counter)
                    print('video_capture.get(cv2.CAP_PROP_POS_FRAMES)', video_capture.get(cv2.CAP_PROP_POS_FRAMES))
                    raise IOError('Failed to read frame!')

                # update last frame to be the current frame
                last_frame = frame

            pausing = True
            update_trackbar_state(current_frame_index)
        # if '-' or '<' key is pressed, decrement the frame index and pause the video
        elif key == ord('-') or key == ord('<') or key == 81:
            # Previous frame feature
            # If the video is paused, decrease the frame by 1 and store the frame in the last_frame for displaying on the next iteration.
            # If the current frame is the first frame, do nothing.
            # If the video is playing, pause the video and display the previous frame.
            # If the current frame is not the first frame, pause the video and display the previous frame.

            # if the current frame is not the first frame
            if current_frame_index > 0:
                if current_frame_index > NUMBER_OF_FRAMES:
                    current_frame_index = NUMBER_OF_FRAMES-1
                    video_capture.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)
                    ret, frame = video_capture.read()
                    if not ret:
                        print('frame index:', current_frame_index, 'frame count:', NUMBER_OF_FRAMES)
                        print('loop_counter:', loop_counter)
                        print('video_capture.get(cv2.CAP_PROP_POS_FRAMES)', video_capture.get(cv2.CAP_PROP_POS_FRAMES))
                        raise IOError('Failed to read frame!')
                    last_frame = frame
                    update_trackbar_state(current_frame_index)
                else:
                    current_frame_index -= 1
                    video_capture.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)
                    ret, frame = video_capture.read()
                    if not ret:
                        print('frame index:', current_frame_index, 'frame count:', NUMBER_OF_FRAMES)
                        print('loop_counter:', loop_counter)
                        print('video_capture.get(cv2.CAP_PROP_POS_FRAMES)', video_capture.get(cv2.CAP_PROP_POS_FRAMES))
                        raise IOError('Failed to read frame!')
                    last_frame = frame
                    update_trackbar_state(current_frame_index)

            pausing = True
        # if 'p' is pressed print the current_frame_index and convert it to the timestamp.
        elif key == ord('p'):
            next_frame_index = video_capture.get(cv2.CAP_PROP_POS_FRAMES)
            current_frame_index = next_frame_index - 1
            if current_frame_index < 0:
                # TODO reason about opencv video frame indexing
                current_frame_index = 0

            print('frame index:', current_frame_index, 'frame count:', NUMBER_OF_FRAMES)
            print('loop_counter:', loop_counter)
            print('video_capture.get(cv2.CAP_PROP_POS_FRAMES)', video_capture.get(cv2.CAP_PROP_POS_FRAMES))

            # print the timestamp in HH:mm:ss.SSS format
            video_timestamp_secs = current_frame_index / VIDEO_FPS
            parsed_timestamp_dict = parse_secs(video_timestamp_secs)
            num_hours = parsed_timestamp_dict['hours']
            num_mins = parsed_timestamp_dict['mins']
            num_secs = parsed_timestamp_dict['seconds']
            num_secs_integer_part = int(num_secs)
            num_secs_fractional_part = (num_secs - num_secs_integer_part)
            print(f'{num_hours}:{num_mins:02}:{num_secs_integer_part:02}.{int(num_secs_fractional_part*1000):03}')
        elif key == 255:
            pass
        else:
            print(f'Unknown key {key} pressed')
    except:
        # print debug info and re-raise exception
        print('frame index:', current_frame_index, 'frame count:', NUMBER_OF_FRAMES)
        print('loop_counter:', loop_counter)
        print('video_capture.get(cv2.CAP_PROP_POS_FRAMES)', video_capture.get(cv2.CAP_PROP_POS_FRAMES))
        raise
