"""Orchestration for PDFs that contain one or more Equatorial invoices."""

import logging
import re

from app.core import extractor, pdf_reader


logger = logging.getLogger(__name__)

# The real Equatorial batch uses this header once per invoice.  Matching only
# its stable prefix also tolerates the different Unicode representations of
# "TENSÃO" produced by PDF text extractors.
INVOICE_START = re.compile(r"GRUPO\s*DE\s*TENS\w*\s*:", re.IGNORECASE)


def _split_invoice_page_groups(pages: list[str]) -> list[list[tuple[int, str]]]:
    """Return only pages that are valid individual-invoice fronts.

    Validation happens before extraction and independently for every physical
    PDF page. Pages without the characteristic invoice header are discarded,
    so grouped-document summaries and invoice backs cannot contribute fields.
    """
    blocks: list[list[tuple[int, str]]] = []

    for page_number, page_text in enumerate(pages, start=1):
        if not INVOICE_START.search(page_text):
            logger.debug(
                "Ignoring page %s: it is not an individual-invoice front.",
                page_number,
            )
            continue
        blocks.append([(page_number, page_text)])

    return blocks


def split_invoice_pages(pages: list[str]) -> list[str]:
    """Return the validated individual-invoice pages for extraction."""
    page_groups = _split_invoice_page_groups(pages)

    invoice_blocks = ["\n".join(text for _, text in group) for group in page_groups]
    logger.debug("PDF pages split into %s invoice blocks.", len(invoice_blocks))
    return invoice_blocks


def process_invoice_pages(pages: list[str]) -> list[dict]:
    """Reuse the current single-invoice extractor for every invoice block."""
    page_groups = _split_invoice_page_groups(pages)
    logger.debug(
        "PDF diagnostic: total pages=%s; invoices identified=%s.",
        len(pages),
        len(page_groups),
    )

    invoices = []
    for invoice_number, page_group in enumerate(page_groups, start=1):
        invoice_text = "\n".join(text for _, text in page_group)
        first_page = page_group[0][0]
        last_page = page_group[-1][0]
        logger.debug(
            "Invoice %s: pages=%s-%s; text length=%s characters.",
            invoice_number,
            first_page,
            last_page,
            len(invoice_text),
        )
        logger.debug("===== RAW INVOICE %s =====\n%s", invoice_number, invoice_text)
        invoices.append(extractor.extract_fields(invoice_text))

    # Do not deduplicate here.  Separate invoices may share a UC and reference
    # month, and the contract is one extracted record per invoice in the PDF.
    return invoices


def process_pdf_with_multiple_invoices(pdf_path: str) -> list[dict]:
    """Read, split, and extract all invoices in a PDF."""
    return process_invoice_pages(pdf_reader.read_pdf_pages(pdf_path))
