# Leitor de Faturas de Energia Equatorial para Excel

Esta é uma aplicação web local desenvolvida em Python para automatizar a leitura, interpretação e consolidação de faturas de energia elétrica da distribuidora **Equatorial** em planilhas Excel.

---

## Recursos Principais

- **Upload Múltiplo**: Selecione ou arraste e solte várias faturas em PDF ao mesmo tempo.
- **Extração Inteligente (Heurísticas)**: Lê os PDFs usando a biblioteca `pdfplumber` e extrai automaticamente:
  - Unidade Consumidora (UC) e Instalação
  - Nome do Titular e CPF/CNPJ
  - Endereço da Unidade Consumidora
  - Mês de Referência, Emissão e Vencimento da fatura
  - Consumo (kWh) e Leituras (Anterior e Atual)
  - Tarifa, Contribuição de Iluminação Pública (COSIP/CIP) e Outros Valores (juros, multas)
- **Editor Embutido**: Edite qualquer dado extraído diretamente na tabela da interface antes de exportar.
- **Console de Logs**: Visualize o status individual de sucesso e erro de cada arquivo.
- **Exportação Premium para Excel**:
  - Salva em arquivo `.xlsx` sem duplicar faturas (utiliza UC + Referência como chaves exclusivas).
  - Formata células corretamente (datas reais, valores monetários formatados como moeda BRL, e números).
  - Preserva zeros à esquerda para CPFs/CNPJs e UCs.
  - Estilização premium da planilha com cabeçalhos profissionais, autoajuste de largura de coluna e efeito zebra.

---

## Estrutura do Projeto

```text
├── app/
│   ├── __init__.py
│   ├── server.py              # Servidor Flask com endpoints da API
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pdf_reader.py      # Leitura estruturada de PDFs
│   │   ├── extractor.py       # Extração de campos via regex e heurísticas
│   │   ├── normalizer.py      # Limpeza, validação e tipagem de dados
│   │   └── excel_writer.py    # Geração de Excel formatado e sem duplicados
│   ├── templates/
│   │   └── index.html         # Template HTML5 da interface
│   └── static/
│       ├── css/
│       │   └── style.css      # Estilização moderna e responsiva (Dark theme)
│       └── js/
│           └── app.js         # Lógica da interface, uploads e tabela editável
├── tests/
│   ├── __init__.py
│   └── test_extractor.py      # Testes unitários do extrator e normalizador
├── uploads/                   # Diretório de uploads temporários
├── requirements.txt           # Dependências do projeto
├── run.py                     # Script de inicialização da aplicação
└── README.md                  # Instruções de uso
```

---

## Instalação e Execução

### Pré-requisitos
- Python 3.10 ou superior instalado.

### Passo 1: Ativar o Ambiente Virtual
No terminal do Windows, navegue até a pasta do projeto e execute:
```powershell
# Ativação do ambiente virtual pré-configurado
.\.venv\Scripts\activate
```

### Passo 2: Executar a Aplicação
Inicie o servidor Flask executando o script principal:
```bash
python run.py
```

Você verá a seguinte saída no terminal:
```text
==================================================
  Leitor de Faturas Equatorial - Iniciando...
  Acesse a aplicação em: http://127.0.0.1:5000
==================================================
```

### Passo 3: Testar e Usar
1. Abra seu navegador em `http://127.0.0.1:5000`.
2. Arraste arquivos PDF da Equatorial reais ou selecione-os na caixa de upload.
3. Clique em **Analisar Faturas**.
4. Veja os dados na tabela e ajuste quaisquer informações clicando duas vezes sobre a célula.
5. Clique em **Exportar para Excel** para baixar o arquivo `.xlsx` gerado.

---

## Executando os Testes Automatizados

Caso queira validar as rotas de extração de dados e normalização, execute o `pytest`:
```bash
# Com o ambiente virtual ativo
python -m pytest
```
Todos os testes mockados passarão com 100% de sucesso.
