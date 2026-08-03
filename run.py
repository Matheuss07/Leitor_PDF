import os
import sys

# Garante que o diretório atual está no path do Python
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.server import app

if __name__ == '__main__':
    print("==================================================")
    print("  Leitor de Faturas Equatorial - Iniciando...")
    print("  Acesse a aplicação em: http://127.0.0.1:5000")
    print("==================================================")
    
    # Executa o servidor Flask na porta 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
