import io

from pypdf import PdfReader

from src.domain.exceptions import InfrastructureException
from src.domain.interfaces import LogProvider, PDFProcessorService


class PDFProcessorServiceInfrastruture(PDFProcessorService):
    def __init__(self, log_provider: LogProvider):
        self.log_provider = log_provider

    def extract_text(self, file_bytes: bytes) -> str:
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)

            extracted_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
            return extracted_text
        except Exception as e:
            self.log_provider.error_log(message="error extracting text", context=str(e))
            raise InfrastructureException("error extracting text") from e

    def split_into_chunks(self, text: str) -> list[str]:
        chunks = []
        start = 0
        text_length = len(text)
        chunk_size = 500
        overlap = 50
        try:
            while start < text_length:
                end = start + chunk_size
                chunk = text[start:end]
                chunks.append(chunk)
                start += chunk_size - overlap

            return chunks
        except Exception as e:
            self.log_provider.error_log(
                message="error spliting text into chunks", context=str(e)
            )
            raise InfrastructureException("error spliting text into chunks") from e
