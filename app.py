<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Refugos - UFE</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- SheetJS (Leitor de Excel) -->
    <script src="https://unpkg.com/xlsx/dist/xlsx.full.min.js"></script>
    <style>
        body { font-family: 'Inter', system-ui, -apple-system, sans-serif; }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen p-6">

    <!-- Cabeçalho -->
    <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 border-b border-slate-800 pb-4">
        <div>
            <h1 class="text-2xl font-bold flex items-center gap-2 text-white">
                <i data-lucide="alert-triangle" class="text-amber-500"></i>
                Dashboard Refugos - UFE
            </h1>
            <p class="text-slate-400 text-sm mt-1">Monitoramento de perdas operacionais e análise de causa raiz</p>
        </div>

        <!-- Área de Importação de Arquivo -->
        <div class="flex flex-wrap items-center gap-3 bg-slate-800 p-3 rounded-xl border border-slate-700">
            <label class="flex items-center gap-2 text-sm font-medium text-slate-200 cursor-pointer bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition">
                <i data-lucide="upload" class="w-4 h-4"></i>
                Importar Arquivo
                <input type="file" id="fileInput" accept=".csv, .txt, .xlsx, .xls" class="hidden" />
            </label>
            <span id="fileName" class="text-xs text-slate-400 max-w-[180px] truncate">Nenhum arquivo selecionado</span>
        </div>
    </header>

    <!-- Cards de KPIs (Topo) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="bg-slate-800 border border-slate-700/60 p-5 rounded-xl shadow-lg">
            <div class="flex items-center justify-between text-slate-400 mb-2">
                <span class="text-sm font-medium">Total Refugado</span>
                <i data-lucide="package-x" class="text-red-400 w-5 h-5"></i>
            </div>
            <div class="text-3xl font-bold text-white" id="kpiTotalRefugado">0 <span class="text-xs font-normal text-slate-400">pçs</span></div>
            <p class="text-xs text-slate-400 mt-2">Volume total de peças perdidas</p>
        </div>

        <div class="bg-slate-800 border border-slate-700/60 p-5 rounded-xl shadow-lg">
            <div class="flex items-center justify-between text-slate-400 mb-2">
                <span class="text-sm font-medium">Taxa de Refugo Geral</span>
                <i data-lucide="percent" class="text-amber-400 w-5 h-5"></i>
            </div>
            <div class="text-3xl font-bold text-amber-400" id="kpiTaxaRefugo">0.0%</div>
            <p class="text-xs text-slate-400 mt-2">Meta estipulada: <strong class="text-slate-200">1.5%</strong></p>
        </div>

        <div class="bg-slate-800 border border-slate-700/60 p-5 rounded-xl shadow-lg">
            <div class="flex items-center justify-between text-slate-400 mb-2">
                <span class="text-sm font-medium">Custo Total do Refugo</span>
                <i data-lucide="dollar-sign" class="text-emerald-400 w-5 h-5"></i>
            </div>
            <div class="text-3xl font-bold text-white" id="kpiCustoTotal">R$ 0,00</div>
            <p class="text-xs text-slate-400 mt-2">Impacto financeiro acumulado</p>
        </div>

        <div class="bg-slate-800 border border-slate-700/60 p-5 rounded-xl shadow-lg">
            <div class="flex items-center justify-between text-slate-400 mb-2">
                <span class="text-sm font-medium">Total Produzido</span>
                <i data-lucide="cpu" class="text-blue-400 w-5 h-5"></i>
            </div>
            <div class="text-3xl font-bold text-white" id="kpiTotalProduzido">0 <span class="text-xs font-normal text-slate-400">pçs</span></div>
            <p class="text-xs text-slate-400 mt-2">Volume de produção processado</p>
        </div>
    </div>

    <!-- Gráficos -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div class="bg-slate-800 border border-slate-700/60 p-5 rounded-xl shadow-lg">
            <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <i data-lucide="bar-chart-2" class="w-5 h-5 text-blue-400"></i>
                Pareto: Motivos de Refugo
            </h2>
            <div class="h-64">
                <canvas id="paretoChart"></canvas>
            </div>
        </div>

        <div class="bg-slate-800 border border-slate-700/60 p-5 rounded-xl shadow-lg">
            <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <i data-lucide="line-chart" class="w-5 h-5 text-emerald-400"></i>
                Evolução Temporal (%) vs Meta
            </h2>
            <div class="h-64">
                <canvas id="trendChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Tabela Detalhada -->
    <div class="bg-slate-800 border border-slate-700/60 rounded-xl shadow-lg overflow-hidden">
        <div class="p-5 border-b border-slate-700/60">
            <h2 class="text-lg font-semibold text-white flex items-center gap-2">
                <i data-lucide="list" class="w-5 h-5 text-amber-400"></i>
                Detalhamento por Máquina / Posto
            </h2>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-slate-300">
                <thead class="bg-slate-900/50 text-slate-400 uppercase text-xs">
                    <tr>
                        <th class="p-4">Posto / Máquina</th>
                        <th class="p-4">Qtd Produzida</th>
                        <th class="p-4">Qtd Refugada</th>
                        <th class="p-4">Taxa (%)</th>
                        <th class="p-4">Custo Refugo</th>
                        <th class="p-4">Status</th>
                    </tr>
                </thead>
                <tbody id="tableBody" class="divide-y divide-slate-700/50">
                    <tr>
                        <td colspan="6" class="p-4 text-center text-slate-500">Nenhum dado importado. Por favor, carregue um arquivo.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        lucide.createIcons();

        let paretoChart, trendChart;

        // Inicialização dos Gráficos Vazios
        function initCharts() {
            const paretoCtx = document.getElementById('paretoChart').getContext('2d');
            paretoChart = new Chart(paretoCtx, {
                type: 'bar',
                data: { labels: [], datasets: [{ label: 'Qtd Refugada', data: [], backgroundColor: '#3b82f6', borderRadius: 6 }] },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } } } }
            });

            const trendCtx = document.getElementById('trendChart').getContext('2d');
            trendChart = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        { label: 'Taxa Refugo (%)', data: [], borderColor: '#f59e0b', borderWidth: 3, tension: 0.3 },
                        { label: 'Meta (1.5%)', data: [], borderColor: '#ef4444', borderWidth: 2, borderDash: [5, 5], pointRadius: 0 }
                    ]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } } } }
            });
        }
        initCharts();

        // Leitura de Arquivo CSV ou Excel (O Novo Motor)
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            document.getElementById('fileName').textContent = file.name;
            const fileName = file.name.toLowerCase();
            const reader = new FileReader();

            if (fileName.endsWith('.csv') || fileName.endsWith('.txt')) {
                reader.onload = function(evt) {
                    processCSV(evt.target.result);
                };
                reader.readAsText(file);
            } 
            else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
                reader.onload = function(evt) {
                    const data = new Uint8Array(evt.target.result);
                    const workbook = XLSX.read(data, {type: 'array'});
                    const worksheet = workbook.Sheets[workbook.SheetNames[0]];
                    // Converte Excel para CSV e envia para a mesma função processar
                    processCSV(XLSX.utils.sheet_to_csv(worksheet));
                };
                reader.readAsArrayBuffer(file);
            } else {
                alert("Por favor, envie um arquivo .csv, .xls ou .xlsx");
            }
        });

        // Função que processa os dados (A mesma de antes)
        function processCSV(csvText) {
            const lines = csvText.trim().split('\n');
            if (lines.length < 2) return;

            const rows = lines.slice(1).map(line => {
                const cols = line.split(/[,;\t]/).map(c => c.trim());
                return {
                    data: cols[0],
                    turno: cols[1],
                    maquina: cols[2],
                    qtdProduzida: parseFloat(cols[3]) || 0,
                    qtdRefugada: parseFloat(cols[4]) || 0,
                    motivo: cols[5] || 'Outros',
                    custoUnitario: parseFloat(cols[6]) || 0
                };
            });
            updateDashboard(rows);
        }

        function updateDashboard(data) {
            let totalProduzido = 0;
            let totalRefugado = 0;
            let custoTotal = 0;
            const motivosMap = {};
            const datasMap = {};
            const maquinasMap = {};

            data.forEach(item => {
                totalProduzido += item.qtdProduzida;
                totalRefugado += item.qtdRefugada;
                custoTotal += (item.qtdRefugada * item.custoUnitario);

                // Agrupamento por Motivo
                motivosMap[item.motivo] = (motivosMap[item.motivo] || 0) + item.qtdRefugada;

                // Agrupamento por Data
                if (!datasMap[item.data]) datasMap[item.data] = { prod: 0, ref: 0 };
                datasMap[item.data].prod += item.qtdProduzida;
                datasMap[item.data].ref += item.qtdRefugada;

                // Agrupamento por Máquina
                if (!maquinasMap[item.maquina]) maquinasMap[item.maquina] = { prod: 0, ref: 0, custo: 0 };
                maquinasMap[item.maquina].prod += item.qtdProduzida;
                maquinasMap[item.maquina].ref += item.qtdRefugada;
                maquinasMap[item.maquina].custo += (item.qtdRefugada * item.custoUnitario);
            });

            const taxaGeral = totalProduzido > 0 ? ((totalRefugado / totalProduzido) * 100).toFixed(2) : 0;

            // Atualiza KPIs
            document.getElementById('kpiTotalRefugado').innerHTML = `${totalRefugado.toLocaleString('pt-BR')} <span class="text-xs font-normal text-slate-400">pçs</span>`;
            document.getElementById('kpiTaxaRefugo').textContent = `${taxaGeral}%`;
            document.getElementById('kpiCustoTotal').textContent = custoTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            document.getElementById('kpiTotalProduzido').innerHTML = `${totalProduzido.toLocaleString('pt-BR')} <span class="text-xs font-normal text-slate-400">pçs</span>`;

            // Atualiza Pareto
            const sortedMotivos = Object.entries(motivosMap).sort((a,b) => b[1] - a[1]);
            paretoChart.data.labels = sortedMotivos.map(m => m[0]);
            paretoChart.data.datasets[0].data = sortedMotivos.map(m => m[1]);
            paretoChart.update();

            // Atualiza Tendência
            const sortedDatas = Object.keys(datasMap).sort();
            const taxasDiarias = sortedDatas.map(d => {
                const prod = datasMap[d].prod;
                return prod > 0 ? ((datasMap[d].ref / prod) * 100).toFixed(2) : 0;
            });
            trendChart.data.labels = sortedDatas;
            trendChart.data.datasets[0].data = taxasDiarias;
            trendChart.data.datasets[1].data = sortedDatas.map(() => 1.5);
            trendChart.update();

            // Atualiza Tabela
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            Object.keys(maquinasMap).forEach(maq => {
                const m = maquinasMap[maq];
                const taxa = m.prod > 0 ? ((m.ref / m.prod) * 100).toFixed(2) : 0;
                
                let statusBadge = '<span class="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs font-medium">Dentro da Meta</span>';
                if (taxa > 1.5) {
                    statusBadge = '<span class="px-2.5 py-1 bg-red-500/10 text-red-400 rounded-full text-xs font-medium">Acima da Meta</span>';
                }

                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-700/30 transition';
                tr.innerHTML = `
                    <td class="p-4 font-medium text-white">${maq}</td>
                    <td class="p-4">${m.prod.toLocaleString('pt-BR')}</td>
                    <td class="p-4 text-red-400 font-semibold">${m.ref.toLocaleString('pt-BR')}</td>
                    <td class="p-4">${taxa}%</td>
                    <td class="p-4">${m.custo.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                    <td class="p-4">${statusBadge}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    </script>
</body>
</html>
