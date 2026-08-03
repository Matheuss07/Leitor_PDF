import json
from unittest.mock import patch
import pytest
from app.server import app
from tests.test_invoice_processor import INVOICE_1_TEXT, INVOICE_2_TEXT

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """Test that the index page loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Equatorial PDF" in response.data


@patch("app.core.pdf_reader.read_pdf_pages")
def test_api_process_single_invoice(mock_read_pages, client):
    """Test /api/process endpoint when a PDF contains a single invoice."""
    mock_read_pages.return_value = [INVOICE_1_TEXT]

    # Create dummy upload entry
    with patch("os.path.exists", return_value=True):
        response = client.post(
            "/api/process",
            data=json.dumps({"files": ["single.pdf"]}),
            content_type="application/json",
        )

    assert response.status_code == 200
    res_data = json.loads(response.data)
    assert "results" in res_data
    assert len(res_data["results"]) == 1
    
    result = res_data["results"][0]
    assert result["status"] == "success"
    assert result["filename"] == "single.pdf"
    
    invoices = result["data"]
    assert isinstance(invoices, list)
    assert len(invoices) == 1
    assert invoices[0]["cliente"] == "MUNICIPIO DE FLEXEIRAS"
    assert invoices[0]["uc"] == "669.008.008-24"


@patch("app.core.pdf_reader.read_pdf_pages")
def test_api_process_multiple_invoices(mock_read_pages, client):
    """Test /api/process endpoint when a PDF contains multiple invoices."""
    mock_read_pages.return_value = [INVOICE_1_TEXT, INVOICE_2_TEXT]

    # Create dummy upload entry
    with patch("os.path.exists", return_value=True):
        response = client.post(
            "/api/process",
            data=json.dumps({"files": ["multiple.pdf"]}),
            content_type="application/json",
        )

    assert response.status_code == 200
    res_data = json.loads(response.data)
    assert "results" in res_data
    assert len(res_data["results"]) == 1
    
    result = res_data["results"][0]
    assert result["status"] == "success"
    assert result["filename"] == "multiple.pdf"
    
    invoices = result["data"]
    assert isinstance(invoices, list)
    assert len(invoices) == 2
    assert invoices[0]["cliente"] == "MUNICIPIO DE FLEXEIRAS"
    assert invoices[0]["uc"] == "669.008.008-24"
    assert invoices[1]["cliente"] == "MUNICIPIO DE MACEIO"
    assert invoices[1]["uc"] == "111.222.333-44"


@patch("app.core.pdf_reader.read_pdf_pages")
def test_api_process_empty_or_scanned_pdf(mock_read_pages, client):
    """Test /api/process endpoint handles scanned or empty PDF properly."""
    mock_read_pages.return_value = []

    with patch("os.path.exists", return_value=True):
        response = client.post(
            "/api/process",
            data=json.dumps({"files": ["empty.pdf"]}),
            content_type="application/json",
        )

    assert response.status_code == 200
    res_data = json.loads(response.data)
    assert len(res_data["results"]) == 1
    
    result = res_data["results"][0]
    assert result["status"] == "error"
    assert "PDF sem texto selecionável" in result["error"]


def test_api_export_excel(client):
    """Test /api/export endpoint generates file response."""
    test_items = [
        {
            "filename": "faturas.pdf - Fatura 1",
            "uc": "669.008.008-24",
            "cliente": "MUNICIPIO DE FLEXEIRAS",
            "medidor": "E2005221",
            "local_unidade": "CASA DA MERENDA",
            "conta_mes": "06/2026",
            "vencimento": "2026-07-23",
            "classificacao": "PODER PÚBLICO",
            "subclasse": "MUNICIPAL",
            "tipo_fornecimento": "MONOFÁSICO",
            "leitura_anterior": 32690,
            "leitura_atual": 32985,
            "consumo_kwh": 295.0,
            "total_pagar": 349.64,
        }
    ]

    with patch("app.core.excel_writer.write_to_excel") as mock_write:
        mock_write.return_value = "export/faturas_consolidadas.xlsx"
        
        with patch("app.server.send_file") as mock_send_file:
            mock_send_file.return_value = "mock_excel_file_stream"
            
            response = client.post(
                "/api/export",
                data=json.dumps({"items": test_items}),
                content_type="application/json",
            )
            
            assert response.status_code == 200
            assert response.data == b"mock_excel_file_stream"
            mock_write.assert_called_once()
