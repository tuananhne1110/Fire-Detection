from modules.pipeline import Pipeline

import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.start()