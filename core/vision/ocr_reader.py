import easyocr

class OCRReader:
    def __init__(self, languages=['en']):
        self.reader = easyocr.Reader(languages, gpu=False)

    def read_text(self, image_path: str):
        results = self.reader.readtext(image_path)

        extracted_text = []

        for (bbox, text, confidence) in results:
            extracted_text.append({
                "text": text,
                "confidence": round(float(confidence), 3),
                "bbox": bbox
            })

        return extracted_text
