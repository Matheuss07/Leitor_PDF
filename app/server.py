import os
import logging
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from app.core import pdf_reader, extractor, excel_writer, invoice_processor


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Como index.html em templates/ e js/css em static/, definimos as pastas corretas
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'chave-local-desenvolvimento'
)


UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


EXCEL_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'export'))
os.makedirs(EXCEL_FOLDER, exist_ok=True)
app.config['EXCEL_FOLDER'] = EXCEL_FOLDER

@app.route('/')
def index():
    """Renderiza a pÃ¡gina principal do aplicativo."""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Recebe faturas em PDF enviadas pelo usuÃ¡rio.
    Salva temporariamente no servidor e retorna a lista de arquivos salvos.
    """
    if 'files' not in request.files:
        logger.warning("Nenhum arquivo enviado no corpo da requisiÃ§Ã£o.")
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
    uploaded_files = request.files.getlist('files')
    saved_files = []
    
    for file in uploaded_files:
        if file.filename == '':
            continue
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            saved_files.append({
                "filename": filename,
                "path": file_path
            })
            logger.info(f"Arquivo salvo temporariamente: {filename}")
            
    if not saved_files:
        return jsonify({"error": "Nenhum arquivo PDF vÃ¡lido foi enviado."}), 400
        
    return jsonify({
        "message": f"{len(saved_files)} arquivos carregados com sucesso.",
        "files": [f["filename"] for f in saved_files]
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    """
    Processa a lista de arquivos PDF carregados.
    LÃª o PDF, extrai os campos e retorna o resultado em JSON.
    """
    data = request.get_json() or {}
    filenames = data.get('files', [])
    
    if not filenames:
        logger.warning("Nenhum arquivo especificado para processamento.")
        return jsonify({"error": "Nenhum arquivo para processar"}), 400
        
    results = []
    
    for filename in filenames:
        # Garante seguranÃ§a do arquivo
        safe_name = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
        
        if not os.path.exists(file_path):
            results.append({
                "filename": filename,
                "status": "error",
                "error": "Arquivo nÃ£o encontrado no servidor.",
                "data": None
            })
            continue
            
        try:
            # 1. Processa faturas no PDF (pode conter uma ou mais)
            invoices = invoice_processor.process_pdf_with_multiple_invoices(file_path)
            
            if not invoices:
                # Verifica se pelo menos extraiu algum texto para diferenciar erro de "PDF vazio/digitalizado"
                pages_text = pdf_reader.read_pdf_pages(file_path)
                has_text = any(p.strip() for p in pages_text)
                
                error_msg = (
                    "PDF sem texto selecionÃ¡vel. O arquivo pode ser digitalizado ou imagem."
                    if not has_text
                    else "Nenhuma fatura no padrÃ£o Equatorial foi identificada no arquivo."
                )
                
                results.append({
                    "filename": filename,
                    "status": "error",
                    "error": error_msg,
                    "data": None
                })
                continue
                
            # Adiciona o nome do arquivo para cada fatura
            for inv in invoices:
                inv["filename"] = filename
                
            results.append({
                "filename": filename,
                "status": "success",
                "error": None,
                "data": invoices
            })
            
        except Exception as e:
            logger.exception(f"Erro ao processar o arquivo {filename}: {str(e)}")
            results.append({
                "filename": filename,
                "status": "error",
                "error": f"Falha na anÃ¡lise: {str(e)}",
                "data": None
            })
            
    return jsonify({"results": results})

@app.route('/api/export', methods=['POST'])
def export_excel():
    """
    Recebe os dados extraÃ­dos (potencialmente modificados pelo usuÃ¡rio)
    e gera a planilha Excel formatada para download.
    """
    data = request.get_json() or {}
    items = data.get('items', [])
    
    if not items:
        logger.warning("Tentativa de exportaÃ§Ã£o com lista de dados vazia.")
        return jsonify({"error": "Nenhum dado fornecido para exportaÃ§Ã£o"}), 400
        
    # Define o caminho do arquivo Excel final consolidado
    excel_filename = "faturas_processadas.xlsx"
    excel_path = os.path.join(app.config['EXCEL_FOLDER'], excel_filename)
    
    try:
        # Grava os dados no Excel
        saved_path = excel_writer.write_to_excel(items, excel_path)
        logger.info(f"Excel gerado com sucesso: {saved_path}")
        
        # Envia o arquivo de volta para o cliente
        return send_file(
            saved_path,
            as_attachment=True,
            download_name=excel_filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        logger.exception(f"Erro ao gerar a planilha Excel: {str(e)}")
        return jsonify({"error": f"Erro interno ao gerar Excel: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Recurso nÃ£o encontrado"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Erro de servidor: {str(e)}")
    return jsonify({"error": "Erro interno do servidor"}), 500
