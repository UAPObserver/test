from predict import predict_one_image
import os
import ffmpeg
import numpy as np

# Config
home_dir = '/home/d/observer/'



def video_prediction(video_filepath):
    probe = ffmpeg.probe(video_filepath)
    time = float(probe['streams'][0]['duration']) // 2
    width = probe['streams'][0]['width']

    # Set how many spots you want to extract a video from.
    parts = 5

    intervals = time // parts
    intervals = int(intervals)
    interval_list = [(i * intervals, (i + 1) * intervals) for i in range(parts)]
    i = 0


    results = []

    for item in interval_list:
        path = str(home_dir) + "/video_frames/"
        (
            ffmpeg
            .input(video_filepath, ss=item[1])
            #.filter('super2xsai')
            .filter('copy')
            .output(path  + str(i) + '.jpg', vframes=1)
            .overwrite_output()
            .run()
        )

        frame_path = str(path) + str(i) + ".jpg"
        proba, _ = predict_one_image(frame_path)
        results.append(proba)
        i += 1

    print("All floats: ", str(results))
    real =  round((np.mean(results) * 100), 2)
    real_str = "AI Prediction: " + str(real) + "%" + " real"
    print(real_str)
    return real_str


#print(str(video_prediction('test.mp4')))
