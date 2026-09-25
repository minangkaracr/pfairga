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

def test_get_billing_period():
    from datetime import date
    from app.telegram.commands import get_billing_period

    # Test case 1: On the 25th of September (start of new cycle)
    start_d, end_d = get_billing_period(date(2026, 9, 25))
    assert start_d == date(2026, 9, 25)
    assert end_d == date(2026, 10, 24)

    # Test case 2: On the 24th of September (last day of previous cycle)
    start_d, end_d = get_billing_period(date(2026, 9, 24))
    assert start_d == date(2026, 8, 25)
    assert end_d == date(2026, 9, 24)

    # Test case 3: Middle of month (e.g., September 10)
    start_d, end_d = get_billing_period(date(2026, 9, 10))
    assert start_d == date(2026, 8, 25)
    assert end_d == date(2026, 9, 24)

    # Test case 4: December 25th (crossing into new year)
    start_d, end_d = get_billing_period(date(2026, 12, 25))
    assert start_d == date(2026, 12, 25)
    assert end_d == date(2027, 1, 24)

    # Test case 5: January 5th (cycle started in previous year's December)
    start_d, end_d = get_billing_period(date(2027, 1, 5))
    assert start_d == date(2026, 12, 25)
    assert end_d == date(2027, 1, 24)

