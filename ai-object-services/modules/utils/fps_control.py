import time


class FPSTracker:

    def __init__(self, target_fps=None):
        self.fps = 0
        self.frame_count = 0
        self.second_count = 0
        self.start_time = None
        self.target_fps = target_fps

    def __enter__(self):
        self.start_time = time.time()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.frame_count += 1
        self.second_count += time.time() - self.start_time
        self.fps = self.frame_count / self.second_count

        if self.target_fps is None or self.fps <= self.target_fps:
            return

        sleep_time = self.frame_count / self.target_fps - self.second_count
        time.sleep(sleep_time)

        self.second_count += time.time() - self.start_time
        self.fps = self.frame_count / self.second_count


class FPSControl:
    def __init__(self, interval_logs=10, target_fps=15):
        self.fr_count = 0
        self.start_time = time.time()
        self.period_time = time.time()
        self.start_track_time = time.time()
        self.interval_logs = interval_logs
        self.target_fps = target_fps
        self.fps = 0

    def fps_count(self):
        return self.fr_count / (time.time() - self.start_time)

    def keep_target_fps(self, start_track_time):
        sleep_time = 1.0 / self.target_fps - (time.time() - start_track_time)
        if sleep_time > 0:
            time.sleep(sleep_time)

    def reset_params(self):
        self.period_time = time.time()
        self.fr_count = 0
        self.start_time = time.time()
