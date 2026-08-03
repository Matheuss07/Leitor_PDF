import pdfplumber
import logging
import os

logger = logging.getLogger(__name__)


def read_pdf_pages(pdf_path: str) -> list[str]:
    """Read each PDF page independently without interpreting invoice fields."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

    pages_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text(
                    layout=True,
                    x_tolerance=2,
                    y_tolerance=3,
                )
                if page_text:
                    pages_text.append(page_text)
                    logger.info("Texto extraído da página %s", page_number)
                else:
                    # Preserve physical page positions for per-page validation.
                    pages_text.append("")
                    logger.warning("Página %s sem texto selecionável.", page_number)
    except Exception as exc:
        logger.error("Erro ao abrir PDF: %s", exc)
        raise RuntimeError(f"Erro na leitura do PDF: {exc}") from exc

    return pages_text


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrai o texto de todas as páginas do PDF.
    Usa layout=True para tentar preservar a posição
    dos elementos presentes na fatura.
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"Arquivo PDF não encontrado: {pdf_path}"
        )

    logger.info(f"Lendo PDF: {pdf_path}")

    pages_text = []

    try:
        with pdfplumber.open(pdf_path) as pdf:

            for page_number, page in enumerate(pdf.pages, start=1):

                try:
                    # Tenta preservar a estrutura visual
                    page_text = page.extract_text(
                        layout=True,
                        x_tolerance=2,
                        y_tolerance=3,
                    )

                    if page_text:
                        pages_text.append(
                            f"\n--- PÁGINA {page_number} ---\n"
                            f"{page_text}"
                        )

                        logger.info(
                            f"Texto extraído da página {page_number}"
                        )

                    else:
                        logger.warning(
                            f"Página {page_number} sem texto "
                            f"selecionável."
                        )

                except Exception as e:
                    logger.error(
                        f"Erro na página {page_number}: {e}"
                    )

    except Exception as e:
        logger.error(
            f"Erro ao abrir PDF: {e}"
        )

        raise RuntimeError(
            f"Erro na leitura do PDF: {e}"
        )

    full_text = "\n".join(pages_text)

    if not full_text.strip():
        logger.warning(
            "Nenhum texto foi encontrado no PDF."
        )

    return full_text
