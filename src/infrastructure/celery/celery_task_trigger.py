from src.domain.entities import DocumentEntity
from src.domain.interfaces import CeleryTaskService
from src.infrastructure.celery.celery_app import process_pdf


class CeleryTaskServiceInfrastructure(CeleryTaskService):
    def trigger_converting_process_pdf_task(self, user_id: int, pdf: DocumentEntity):
        process_pdf.delay(document_id=pdf.id, user_id=user_id)
