document.addEventListener('DOMContentLoaded', () => {
    // ==========================================================
    // ESTADO DA APLICAÇÃO
    // ==========================================================

    let filesQueue = [];
    let extractedData = [];


    // ==========================================================
    // ELEMENTOS DO DOM
    // ==========================================================

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileListContainer = document.getElementById('file-list-container');
    const fileList = document.getElementById('file-list');
    const fileCount = document.getElementById('file-count');
    const btnClear = document.getElementById('btn-clear');
    const btnProcess = document.getElementById('btn-process');
    const processSpinner = document.getElementById('process-spinner');
    const consoleBox = document.getElementById('console-box');
    const btnExport = document.getElementById('btn-export');
    const emptyState = document.getElementById('empty-state');
    const tableContainer = document.getElementById('table-container');
    const tableBody = document.getElementById('table-body');
    const toastContainer = document.getElementById('toast-container');


    // ==========================================================
    // 1. DRAG AND DROP
    // ==========================================================

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(
            eventName,
            preventDefaults,
            false
        );
    });


    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }


    // Efeito visual ao arrastar arquivo

    ['dragenter', 'dragover'].forEach(eventName => {

        dropZone.addEventListener(
            eventName,
            () => dropZone.classList.add('dragover'),
            false
        );

    });


    ['dragleave', 'drop'].forEach(eventName => {

        dropZone.addEventListener(
            eventName,
            () => dropZone.classList.remove('dragover'),
            false
        );

    });


    // ==========================================================
    // DROP DE ARQUIVOS
    // ==========================================================

    dropZone.addEventListener('drop', (e) => {

        const files = e.dataTransfer.files;

        handleFiles(files);

    });


    // ==========================================================
    // SELEÇÃO MANUAL
    // ==========================================================

    fileInput.addEventListener('change', (e) => {

        handleFiles(e.target.files);

    });


    // ==========================================================
    // TRATAMENTO DOS ARQUIVOS
    // ==========================================================

    function handleFiles(files) {

        const pdfFiles = Array.from(files).filter(file =>

            file.type === 'application/pdf' ||
            file.name.toLowerCase().endsWith('.pdf')

        );


        if (pdfFiles.length === 0) {

            showToast(
                'Nenhum arquivo PDF válido selecionado.',
                'error'
            );

            return;
        }


        // Evita arquivos duplicados

        pdfFiles.forEach(file => {

            const alreadyExists = filesQueue.some(

                f =>
                    f.name === file.name &&
                    f.size === file.size

            );


            if (!alreadyExists) {

                filesQueue.push(file);

                logConsole(

                    `Arquivo adicionado à fila: ${file.name} (${formatBytes(file.size)})`,

                    'info'

                );

            }

        });


        renderFileList();

    }


    // ==========================================================
    // RENDERIZA LISTA DE ARQUIVOS
    // ==========================================================

    function renderFileList() {

        fileList.innerHTML = '';

        fileCount.textContent = filesQueue.length;


        if (filesQueue.length > 0) {

            fileListContainer.classList.remove('hide');


            filesQueue.forEach((file, index) => {

                const li = document.createElement('li');

                li.className = 'file-item';


                li.innerHTML = `

                    <div class="file-info">

                        <div class="file-icon">

                            <svg xmlns="http://www.w3.org/2000/svg"
                                 viewBox="0 0 20 20"
                                 fill="currentColor">

                                <path
                                    fill-rule="evenodd"
                                    d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                                    clip-rule="evenodd"
                                />

                            </svg>

                        </div>

                        <span
                            class="file-name"
                            title="${file.name}"
                        >
                            ${file.name}
                        </span>

                    </div>


                    <button
                        class="btn-remove"
                        data-index="${index}"
                    >

                        <svg xmlns="http://www.w3.org/2000/svg"
                             viewBox="0 0 20 20"
                             fill="currentColor">

                            <path
                                fill-rule="evenodd"
                                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                clip-rule="evenodd"
                            />

                        </svg>

                    </button>

                `;


                fileList.appendChild(li);

            });


            // Remove arquivos

            document.querySelectorAll('.btn-remove').forEach(btn => {

                btn.addEventListener('click', (e) => {

                    const idx = parseInt(
                        e.currentTarget.getAttribute('data-index')
                    );


                    const removedName =
                        filesQueue[idx].name;


                    filesQueue.splice(
                        idx,
                        1
                    );


                    logConsole(

                        `Arquivo removido da fila: ${removedName}`,

                        'warn'

                    );


                    renderFileList();

                });

            });


        } else {

            fileListContainer.classList.add('hide');

        }

    }


    // ==========================================================
    // LIMPAR FILA
    // ==========================================================

    btnClear.addEventListener('click', () => {

        filesQueue = [];

        renderFileList();

        logConsole(
            'Fila de processamento limpa.',
            'system'
        );

        showToast(
            'Fila limpa.',
            'info'
        );

    });


    // ==========================================================
    // 2. PROCESSAMENTO DAS FATURAS
    // ==========================================================

    btnProcess.addEventListener('click', async () => {

        if (filesQueue.length === 0) {

            showToast(
                'Adicione pelo menos um PDF.',
                'error'
            );

            return;
        }


        setLoading(true);


        logConsole(

            `Iniciando upload de ${filesQueue.length} faturas...`,

            'info'

        );


        try {

            // ==================================================
            // UPLOAD
            // ==================================================

            const formData = new FormData();


            filesQueue.forEach(file => {

                formData.append(
                    'files',
                    file
                );

            });


            const uploadRes = await fetch(
                '/api/upload',
                {
                    method: 'POST',
                    body: formData
                }
            );


            if (!uploadRes.ok) {

                const errData =
                    await uploadRes.json();


                throw new Error(

                    errData.error ||
                    'Falha no upload dos arquivos.'

                );

            }


            const uploadResult =
                await uploadRes.json();


            logConsole(

                'Upload concluído. Iniciando análise dos arquivos...',

                'success'

            );


            // ==================================================
            // PROCESSAMENTO
            // ==================================================

            const processRes = await fetch(

                '/api/process',

                {

                    method: 'POST',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body: JSON.stringify({

                        files:
                            uploadResult.files

                    })

                }

            );


            if (!processRes.ok) {

                throw new Error(

                    'Falha no servidor durante o processamento das faturas.'

                );

            }


            const processResult =
                await processRes.json();


            // ==================================================
            // RESULTADOS
            // ==================================================

            handleProcessingResults(

                processResult.results

            );


        } catch (error) {

            logConsole(

                `Erro: ${error.message}`,

                'error'

            );


            showToast(

                error.message,

                'error'

            );


        } finally {

            setLoading(false);

        }

    });


    // ==========================================================
    // PROCESSA RESULTADOS
    // ==========================================================

    function handleProcessingResults(results) {
        let successCount = 0;
        let errorCount = 0;

        results.forEach(res => {
            if (res.status === 'success') {
                const invoicesList = Array.isArray(res.data) ? res.data : [res.data];

                invoicesList.forEach((data, invoiceIndex) => {
                    successCount++;

                    logConsole(
                        `Análise concluída: ${res.filename} | UC: ${data.uc}`,
                        'success'
                    );

                    // Adiciona o nome do arquivo aos dados (com sufixo se houver mais de uma fatura no mesmo arquivo)
                    if (invoicesList.length > 1) {
                        data.filename = `${res.filename} - Fatura ${invoiceIndex + 1}`;
                    } else {
                        data.filename = res.filename;
                    }

                    // Each object returned by the API represents one invoice.
                    // UC and reference month are not unique in grouped PDFs.
                    extractedData.push(data);
                });
            } else {
                errorCount++;

                logConsole(
                    `Erro em [${res.filename}]: ${res.error}`,
                    'error'
                );
            }
        });

        showToast(
            `Processados: ${successCount} com sucesso, ${errorCount} com erros.`,
            successCount > 0
                ? 'success'
                : 'error'
        );

        if (extractedData.length > 0) {
            renderTable();
        }
    }


    // ==========================================================
    // 3. TABELA
    // ==========================================================

    function renderTable() {

        tableBody.innerHTML = '';


        emptyState.classList.add('hide');

        tableContainer.classList.remove('hide');

        btnExport.disabled = false;


        extractedData.forEach((item, index) => {

            const tr =
                document.createElement('tr');


            tr.innerHTML = `

                <td
                    title="${item.filename || ''}"
                >
                    ${item.filename || 'N/A'}
                </td>


                <td
                    class="cell-editable"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="uc"
                >
                    ${item.uc || 'N/A'}
                </td>


                <td
                    class="cell-editable"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="cliente"
                >
                    ${item.cliente || 'N/A'}
                </td>


                <td
                    class="cell-editable"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="medidor"
                >
                    ${item.medidor || 'N/A'}
                </td>


                <td
                    class="cell-editable"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="local_unidade"
                >
                    ${item.local_unidade || 'N/A'}
                </td>


                <td
                    class="cell-editable"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="conta_mes"
                >
                    ${item.conta_mes || 'N/A'}
                </td>


                <td
                    class="cell-editable"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="vencimento"
                >
                    ${item.vencimento || 'N/A'}
                </td>


                <td
                    class="cell-editable"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="classificacao"
                >
                    ${item.classificacao || 'N/A'}
                </td>


                <td
                    class="cell-editable"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="subclasse"
                >
                    ${item.subclasse || 'N/A'}
                </td>


                <td
                    class="cell-editable"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="tipo_fornecimento"
                >
                    ${item.tipo_fornecimento || 'N/A'}
                </td>


                <td
                    class="cell-editable text-right"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="leitura_anterior"
                >
                    ${item.leitura_anterior ?? 0}
                </td>


                <td
                    class="cell-editable text-right"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="leitura_atual"
                >
                    ${item.leitura_atual ?? 0}
                </td>


                <td
                    class="cell-editable text-right"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="consumo_kwh"
                >
                    ${item.consumo_kwh ?? 0}
                </td>


                <td
                    class="cell-editable text-right"
                    contenteditable="true"
                    data-index="${index}"
                    data-field="total_pagar"
                >
                    ${formatBRL(item.total_pagar)}
                </td>


                <td>

                    <button
                        class="btn-remove btn-delete-row"
                        data-row-index="${index}"
                        title="Excluir da lista"
                    >

                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                        >

                            <path
                                fill-rule="evenodd"
                                d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                                clip-rule="evenodd"
                            />

                        </svg>

                    </button>

                </td>

            `;


            tableBody.appendChild(tr);

        });


        // ======================================================
        // EDIÇÃO DAS CÉLULAS
        // ======================================================

        document
            .querySelectorAll('.cell-editable')
            .forEach(cell => {

                cell.addEventListener(
                    'blur',
                    (e) => {

                        const idx =
                            parseInt(
                                e.target
                                    .getAttribute(
                                        'data-index'
                                    )
                            );


                        const field =
                            e.target
                                .getAttribute(
                                    'data-field'
                                );


                        let value =
                            e.target
                                .textContent
                                .trim();


                        // Valores numéricos

                        if (
                            [
                                'leitura_anterior',
                                'leitura_atual',
                                'consumo_kwh'
                            ].includes(field)
                        ) {

                            const numericValue =
                                parseFloat(

                                    value
                                        .replace(
                                            /\./g,
                                            ''
                                        )
                                        .replace(
                                            ',',
                                            '.'
                                        )

                                ) || 0;


                            extractedData[idx][field] =
                                numericValue;


                            e.target.textContent =
                                numericValue;

                        }


                        // Total a pagar

                        else if (
                            field ===
                            'total_pagar'
                        ) {

                            const numericValue =
                                parseFloat(

                                    value
                                        .replace(
                                            /R\$/g,
                                            ''
                                        )
                                        .replace(
                                            /\s/g,
                                            ''
                                        )
                                        .replace(
                                            /\./g,
                                            ''
                                        )
                                        .replace(
                                            ',',
                                            '.'
                                        )

                                ) || 0;


                            extractedData[idx][field] =
                                numericValue;


                            e.target.textContent =
                                formatBRL(
                                    numericValue
                                );

                        }


                        // Texto normal

                        else {

                            extractedData[idx][field] =
                                value;

                        }


                        logConsole(

                            `Célula atualizada: Linha ${idx + 1}, Campo [${field}] ➔ ${extractedData[idx][field]}`,

                            'info'

                        );

                    }
                );


                // Enter salva edição

                cell.addEventListener(
                    'keydown',
                    (e) => {

                        if (e.key === 'Enter') {

                            e.preventDefault();

                            cell.blur();

                        }

                    }
                );

            });


        // ======================================================
        // EXCLUIR LINHA
        // ======================================================

        document
            .querySelectorAll('.btn-delete-row')
            .forEach(btn => {

                btn.addEventListener(
                    'click',
                    (e) => {

                        const idx =
                            parseInt(

                                e.currentTarget
                                    .getAttribute(
                                        'data-row-index'
                                    )

                            );


                        const removedItem =
                            extractedData[idx];


                        extractedData.splice(
                            idx,
                            1
                        );


                        logConsole(

                            `Registro removido: UC ${removedItem.uc} - Conta ${removedItem.conta_mes}`,

                            'warn'

                        );


                        showToast(

                            'Registro removido.',

                            'info'

                        );


                        if (
                            extractedData.length > 0
                        ) {

                            renderTable();

                        } else {

                            hideTable();

                        }

                    }
                );

            });

    }


    // ==========================================================
    // ESCONDER TABELA
    // ==========================================================

    function hideTable() {

        tableContainer.classList.add('hide');

        btnExport.disabled = true;

        emptyState.classList.remove('hide');

    }


    // ==========================================================
    // 4. EXPORTAÇÃO PARA EXCEL
    // ==========================================================

    btnExport.addEventListener(
        'click',
        async () => {

            if (
                extractedData.length === 0
            ) {

                return;

            }


            logConsole(

                'Enviando dados consolidados para geração de planilha Excel...',

                'info'

            );


            showToast(

                'Gerando Excel...',

                'info'

            );


            try {

                const response =
                    await fetch(

                        '/api/export',

                        {

                            method: 'POST',

                            headers: {

                                'Content-Type':
                                    'application/json'

                            },

                            body: JSON.stringify({

                                items:
                                    extractedData

                            })

                        }

                    );


                if (!response.ok) {

                    const errData =
                        await response.json();


                    throw new Error(

                        errData.error ||
                        'Falha ao exportar planilha Excel.'

                    );

                }


                const blob =
                    await response.blob();

                const contentDisposition =
                    response.headers.get('Content-Disposition') || '';

                const filenameMatch =
                    contentDisposition.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i);

                const downloadFilename = filenameMatch
                    ? decodeURIComponent(filenameMatch[1].replace(/\"/g, '').trim())
                    : 'faturas_processadas.xlsx';


                const url =
                    window.URL.createObjectURL(
                        blob
                    );


                const a =
                    document.createElement(
                        'a'
                    );


                a.href = url;

                a.download =
                    downloadFilename;


                document.body.appendChild(a);

                a.click();


                document.body.removeChild(a);

                window.URL.revokeObjectURL(
                    url
                );


                logConsole(

                    'Planilha Excel gerada e baixada com sucesso!',

                    'success'

                );


                showToast(

                    'Planilha gerada com sucesso!',

                    'success'

                );


            } catch (error) {

                logConsole(

                    `Erro ao exportar: ${error.message}`,

                    'error'

                );


                showToast(

                    error.message,

                    'error'

                );

            }

        }
    );


    // ==========================================================
    // 5. LOADING
    // ==========================================================

    function setLoading(isLoading) {

        if (isLoading) {

            btnProcess.disabled = true;

            btnClear.disabled = true;

            processSpinner.classList.remove(
                'hide'
            );

        } else {

            btnProcess.disabled = false;

            btnClear.disabled = false;

            processSpinner.classList.add(
                'hide'
            );

        }

    }


    // ==========================================================
    // LOG
    // ==========================================================

    function logConsole(
        message,
        type = 'info'
    ) {

        const time =
            new Date()
                .toLocaleTimeString();


        const line =
            document.createElement(
                'div'
            );


        line.className =
            `console-line ${type}`;


        line.textContent =
            `[${time}] ${message}`;


        consoleBox.appendChild(
            line
        );


        consoleBox.scrollTop =
            consoleBox.scrollHeight;

    }


    // ==========================================================
    // TOAST
    // ==========================================================

    function showToast(
        message,
        type = 'info'
    ) {

        const toast =
            document.createElement(
                'div'
            );


        toast.className =
            `toast ${type}`;


        toast.textContent =
            message;


        toastContainer.appendChild(
            toast
        );


        setTimeout(
            () => {

                toast.style.animation =
                    'slide-in 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards';


                setTimeout(
                    () => {

                        if (
                            toastContainer.contains(
                                toast
                            )
                        ) {

                            toastContainer.removeChild(
                                toast
                            );

                        }

                    },
                    300
                );

            },
            4000
        );

    }


    // ==========================================================
    // FORMATAR TAMANHO
    // ==========================================================

    function formatBytes(
        bytes,
        decimals = 2
    ) {

        if (bytes === 0) {

            return '0 Bytes';

        }


        const k = 1024;


        const dm =
            decimals < 0
                ? 0
                : decimals;


        const sizes = [

            'Bytes',
            'KB',
            'MB',
            'GB'

        ];


        const i =
            Math.floor(
                Math.log(bytes) /
                Math.log(k)
            );


        return (

            parseFloat(

                (
                    bytes /
                    Math.pow(
                        k,
                        i
                    )
                )
                .toFixed(dm)

            )

            +

            ' ' +

            sizes[i]

        );

    }


    // ==========================================================
    // FORMATA MOEDA BRASILEIRA
    // ==========================================================

    function formatBRL(value) {

        if (
            value === null ||
            value === undefined ||
            isNaN(value)
        ) {

            return 'R$ 0,00';

        }


        return value.toLocaleString(

            'pt-BR',

            {

                style: 'currency',

                currency: 'BRL'

            }

        );

    }

});
