import React, { useState } from 'react';
import { LayoutDashboard, Clock, AlertCircle, CheckCircle2, Search } from 'lucide-react';

interface CargaItem {
  id: string;
  centroTrabalho: string;
  peca: string;
  horasPendentes: number;
  statusAPQ: 'Pendente' | 'Liberado' | 'Em Andamento';
  observacao: string;
}

export function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [dados, setDados] = useState<CargaItem[]>([
    { id: '1', centroTrabalho: 'CT-01', peca: 'Eixo Principal', horasPendentes: 24.5, statusAPQ: 'Pendente', observacao: 'Aguardando material' },
    { id: '2', centroTrabalho: 'CT-02', peca: 'Carcaça Superior', horasPendentes: 12.0, statusAPQ: 'Liberado', observacao: 'Usinagem em curso' },
  ]);

  const dadosFiltrados = dados.filter(item => 
    item.centroTrabalho.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.peca.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <LayoutDashboard className="w-8 h-8 text-blue-500" />
          <h1 className="text-2xl font-bold tracking-tight">Dashboard Horas CT</h1>
        </div>
        <div className="text-sm text-slate-400">Controle de Carga Pendente</div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span>Total de Horas</span>
            <Clock className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {dados.reduce((acc, curr) => acc + curr.horasPendentes, 0).toFixed(1)}h
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span>Centros de Trabalho</span>
            <AlertCircle className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{new Set(dados.map(d => d.centroTrabalho)).size}</div>
        </div>
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span>Itens Liberados (APQ)</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {dados.filter(d => d.statusAPQ === 'Liberado').length}
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <div className="relative w-72">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Filtrar por CT ou Peça..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900/50 text-slate-400 uppercase text-xs tracking-wider border-b border-slate-700">
              <tr>
                <th className="p-3">Centro de Trabalho</th>
                <th className="p-3">Peça</th>
                <th className="p-3">Horas Pendentes</th>
                <th className="p-3">Status APQ</th>
                <th className="p-3">Observação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {dadosFiltrados.map((item) => (
                <tr key={item.id} className="hover:bg-slate-700/50 transition-colors">
                  <td className="p-3 font-medium">{item.centroTrabalho}</td>
                  <td className="p-3">{item.peca}</td>
                  <td className="p-3 font-semibold text-blue-400">{item.horasPendentes}h</td>
                  <td className="p-3">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                      item.statusAPQ === 'Liberado' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                      item.statusAPQ === 'Em Andamento' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                      'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}>
                      {item.statusAPQ}
                    </span>
                  </td>
                  <td className="p-3 text-slate-400">{item.observacao}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
