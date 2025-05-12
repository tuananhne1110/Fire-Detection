import requests
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

class TelegramHandler:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_message(self, message, evidence=None):
        """
        Gửi thông báo đến Telegram.
        
        Yêu cầu bắt buộc phải có evidence (dạng bytes chứa ảnh JPEG).
        Nếu evidence là None, báo lỗi và không gửi cảnh báo.
        
        Nếu evidence khác None, lưu tạm dữ liệu evidence thành file JPEG và gửi ảnh kèm caption.
        """
        if evidence is None:
            error_msg = "No frame provided. Alert cannot be sent without an image frame."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Nếu evidence không None, đảm bảo nó là kiểu bytes.
        if not isinstance(evidence, bytes):
            error_msg = "Evidence must be bytes representing a JPEG image."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Lưu evidence (bytes) thành file tạm thời với đuôi .jpg
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(evidence)
                tmp_file_path = tmp_file.name

            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            with open(tmp_file_path, 'rb') as photo_file:
                files = {'photo': photo_file}
                data = {"chat_id": self.chat_id, "caption": message}
                response = requests.post(url, data=data, files=files)
            
            os.remove(tmp_file_path)  

            logger.debug(f"Response from sendPhoto: {response.status_code} {response.text}")
            if response.status_code == 200:
                logger.info("Telegram photo notification sent successfully")
                print("Notification sent via Telegram (photo):", message)
            else:
                logger.error(f"Telegram photo notification failed with status code {response.status_code}")
                print(f"Failed to send photo notification. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Telegram photo notification exception: {str(e)}")
            print("Telegram send_message exception:", str(e))
