# OpenCV video player

## Features

- seeking each frames with trackbar
- go to the next/previous frame (VLC will often freeze when we try to go through the video frame by frame.)

## Usage

Open the video

```sh
python main.py /path/to/video.ext
```

- Press `space` to pause/resume the video
- Press `+`, `>`, or `→` to go display the next frame (the video will be paused)
- Press `-`, `<`, or `←` to go display the previous frame (the video will be paused)
- Press `p` to print the current frame number and timestamp (useful for cutting video with `ffmpeg`)
