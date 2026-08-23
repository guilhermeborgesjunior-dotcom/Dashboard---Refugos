# ==================== EXIBIÇÃO DA TABELA HTML (COM BOTÃO DE EDITAR E APQ) ====================
    str_lit.subheader(f"📊 Registros Encontrados ({len(df_filtrado)})")
    str_lit.markdown("💡 **Instruções:** Clique na palavra **APQ** para alternar entre **Vermelho (Pendente)** e **Verde (Concluído)**. Utilize o botão **Editar** na última coluna para modificar os dados da linha.")

    # Mapeamento incluindo a nova coluna de Ação/Editar no final
    mapeamento_colunas = {
        col_secao: "Seção",
        col_defeito: "Defeito",
        col_nota: "Nota",
        col_data: "Data",
        col_turno: "Turno",
        col_material: "Material",
        col_desc_mat: "Descrição Material",
        col_ct: "CT Causador",
        col_qtd: "Quantidade",
        col_desc_feito: "Descrição Defeito",
        col_causa: "Causa",
        col_texto_causa: "Texto Causa",
        col_custo: "Custo",
        col_obs: "Observação",
        col_acao: "Ação",
        col_colab: "Colaborador",
        col_prep: "Preparador",
        col_apq: "APQ",
        "acao_editar": "Ações" # Nova coluna de edição após APQ
    }

    html_tabela = """
    <div class="tabela-container-wrapper">
    <style>
        .btn-editar {
            background-color: #3b82f6;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: background 0.2s;
        }
        .btn-editar:hover {
            background-color: #2563eb;
        }
    </style>
    <table id="tabela-refugos">
      <thead>
        <tr>
    """
    
    colunas_validas = [k for k in mapeamento_colunas.keys() if k is not None]
    
    for k in colunas_validas:
        nome_cab = mapeamento_colunas[k]
        html_tabela += f'<th style="padding: 12px 10px; text-align: left; font-weight: 600;">{nome_cab}</th>'
    html_tabela += "</tr></thead><tbody>"

    for idx, row in df_filtrado.iterrows():
        r_id = row['rowid']
        html_tabela += f'<tr onclick="selecionarLinha(this)" data-rowid="{r_id}">'
        
        for k in colunas_validas:
            if k == "acao_editar":
                # Botão de editar exclusivo para a linha contendo o ID do registro (rowid)
                val = f'<button class="btn-editar" onclick="abrirEdicao({r_id})">✏️ Editar</button>'
            elif k == col_nota:
                val = str(row['__nota_com_alerta__']) if '__nota_com_alerta__' in row else str(row[k])
            elif k == col_apq:
                raw_apq = str(row[k]).strip().lower()
                is_concluida = raw_apq in ['concluída', 'concluida', 'concluido', 'sim', '1', 'true']
                cor_inicial = "#27ae60" if is_concluida else "#e74c3c"
                status_inicial = "concluido" if is_concluida else "pendente"
                
                val = f'<span class="apq-toggle" data-status="{status_inicial}" style="color: {cor_inicial};">APQ</span>'
            else:
                val = trata_nulos(row[k])
                if k == col_custo and pd.notna(row[k]):
                    val = formata_custo(row[k])
            
            html_tabela += f'<td style="padding: 10px 10px; white-space: nowrap;">{val}</td>'
        html_tabela += "</tr>"

    html_tabela += """
      </tbody>
    </table>
    </div>

    <script>
    function selecionarLinha(tr) {
        var rows = tr.parentElement.getElementsByTagName('tr');
        for (var i = 0; i < rows.length; i++) {
            rows[i].style.backgroundColor = '';
        }
        tr.style.backgroundColor = '#f1f5f9';
    }

    // Função disparada ao clicar no botão Editar de uma linha específica
    function abrirEdicao(rowid) {
        // Envia o ID da linha selecionada para o Streamlit via query params ou session state simulado
        const queryParams = new URLSearchParams(window.location.search);
        queryParams.set('edit_rowid', rowid);
        window.history.replaceState(null, '', '?' + queryParams.toString());
        
        // Força a atualização do Streamlit disparando um evento nativo
        window.parent.document.dispatchEvent(new Event('streamlit:rerun'));
    }

    // Delegação de eventos robusta para alternar entre vermelho e verde no APQ
    document.addEventListener("click", function(event) {
        if (event.target && event.target.classList.contains("apq-toggle")) {
            event.stopPropagation(); // Impede propagação para a linha
            
            const el = event.target;
            const statusAtual = el.getAttribute("data-status");

            if (statusAtual === "pendente") {
                el.style.color = "#27ae60"; // Verde (Concluído)
                el.setAttribute("data-status", "concluido");
            } else {
                el.style.color = "#e74c3c"; // Vermelho (Pendente)
                el.setAttribute("data-status", "pendente");
            }
        }
    });
    </script>
    """

    str_lit.markdown(html_tabela, unsafe_allow_html=True)
