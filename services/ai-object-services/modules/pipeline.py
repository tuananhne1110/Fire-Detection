import os
from multiprocessing import Process, Queue

from logs.log_handler import logger
from modules.controllers.decode import DecodeController
from modules.controllers.fire_controller import FireController


class Pipeline:
    def __init__(self):
        self.queue_fire = Queue(maxsize=10)
        self.decode_controller = DecodeController(self.queue_fire)
        self.fire_controller = FireController(self.queue_fire)
        self.decode_process = Process(
            target=self.decode_controller.run,
            args=(None,),
        )
        self.fire_process = Process(
            target=self.fire_controller.run,
            args=(None,),
        )

    def start(self):
        logger.debug(f"Pipeline PID: {os.getpid()}")
        self.decode_process.start()
        self.fire_process.start()

        self.decode_process.join()
        self.fire_process.join()
