import logging
logger = logging.getLogger(__name__)

try:
    import easyocr
except ImportError:
    easyocr = None

class OCRReader:
    def __init__(self, languages=['en']):
        if easyocr is None:
            logger.warning("easyocr not installed - OCR disabled")
            self.reader = None
            return
            
        try:
            self.reader = easyocr.Reader(languages, gpu=False)
            logger.info(f"OCR reader initialized for languages: {languages}")
        except Exception as e:
            logger.error(f"Failed to initialize OCR: {e}")
            self.reader = None

    def read_text(self, image_path: str):
        if self.reader is None:
            return []

        try:
            results = self.reader.readtext(image_path)
            extracted_text = []

            for item in results:
                # EasyOCR typically returns a list of tuples: (bbox, text, confidence)
                # But sometimes might vary based on config.
                text = ""
                confidence = 0.0
                bbox = []

                if isinstance(item, (list, tuple)):
                    if len(item) == 3:
                        bbox, text, confidence = item
                    elif len(item) == 2:
                        bbox, text = item
                        confidence = 0.0 # Unknown
                
                if text:
                    extracted_text.append({
                        "text": text,
                        "confidence": round(float(confidence), 3),
                        "bbox": bbox
                    })

            return extracted_text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return []