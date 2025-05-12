class Camera:
    def __init__(self, id, url):
        self.id = id
        self.url = url

    def get_info(self):
        return {
            "id": self.id,
            "url": self.url
        }