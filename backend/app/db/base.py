# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.document import Document  # noqa
from app.models.document_chunk import DocumentChunk  # noqa
