import pytest
from app.storage.local_storage import LocalStorage
from app.reporting.pdf_generator import PDFReportGenerator

@pytest.fixture
def temp_storage(tmp_path):
    return LocalStorage(data_dir=tmp_path)

def test_pdf_report_generation(temp_storage):
    pdf_gen = PDFReportGenerator(temp_storage)
    pdf_bytes = pdf_gen.generate_pdf_report("2026-08-01", "2026-08-31")

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
