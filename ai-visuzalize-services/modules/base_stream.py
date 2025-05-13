import threading
import time

from greenlet import getcurrent as get_ident
from logs.log_handler import logger


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """

    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    threads = {}  # background thread that reads frames from camera
    frame = {}  # current frame is stored here by background thread
    last_access = {}  # time of last client access to the camera
    event = {}

    def __init__(self, device, conn):
        """Start the background camera thread if it isn't running yet."""
        self.unique_name = device
        BaseCamera.event[self.unique_name] = CameraEvent()

        if self.unique_name not in BaseCamera.threads:
            BaseCamera.threads[self.unique_name] = None
        if BaseCamera.threads[self.unique_name] is None:
            BaseCamera.last_access[self.unique_name] = time.time()

            # start background frame thread
            BaseCamera.threads[self.unique_name] = threading.Thread(
                target=self._thread, args=(self.unique_name, conn)
            )
            BaseCamera.threads[self.unique_name].start()

            # wait until frames are available
            while self.get_frame(self.unique_name) is None:
                time.sleep(0)

    def get_frame(self, unique_name):
        """Return the current camera frame."""
        BaseCamera.last_access[unique_name] = time.time()

        # wait for a signal from the camera thread
        BaseCamera.event[unique_name].wait()
        BaseCamera.event[unique_name].clear()

        return BaseCamera.frame[unique_name]

    @staticmethod
    def frames(unique_name, conn):
        """ "Generator that returns frames from the camera."""
        raise RuntimeError("Must be implemented by subclasses.")

    @classmethod
    def _thread(cls, unique_name, conn):
        """Camera background thread."""
        logger.debug(f"Starting camera thread: {unique_name}")
        frames_iterator = cls.frames(unique_name, conn)
        for frame in frames_iterator:
            BaseCamera.frame[unique_name] = frame
            BaseCamera.event[unique_name].set()  # send signal to clients
            time.sleep(0)

            # if there hasn't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            if time.time() - BaseCamera.last_access[unique_name] > 5:
                frames_iterator.close()
                logger.debug(f"Stopping camera {unique_name} thread due to inactivity.")
                break
        BaseCamera.threads[unique_name] = None
