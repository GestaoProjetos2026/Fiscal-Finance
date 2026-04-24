import sys
import os
import json
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox,
    QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont
from PyQt6 import uic

# ── Inicia o servidor Flask (api.py) como processo filho separado ──
# Evita conflito de nomes e separa a API REST da UI desktop
_API_APP = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "api.py")
)
_API_DIR = os.path.dirname(_API_APP)

_api_process = subprocess.Popen(
    [sys.executable, _API_APP],
    cwd=_API_DIR,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

import database

# Configuração de caminho para o executável
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. CARREGA O DESENHO DA TELA (.ui)
        uic.loadUi(resource_path("tela_principal.ui"), self)
        
        # Inicia o Banco de Dados
        database.init_db()
        
        # 2. CONECTA FUNCIONALIDADES AOS BOTÕES
        
        # --- Aba 1: Produtos ---
        if hasattr(self, 'btn_salvar_produto'):
            self.btn_salvar_produto.clicked.connect(self.acao_salvar_produto)
            
        if hasattr(self, 'btn_excluir_produto'):
            self.btn_excluir_produto.clicked.connect(self.acao_excluir_produto)
            
        if hasattr(self, 'btn_listar_produtos'):
            self.btn_listar_produtos.clicked.connect(self.acao_listar_produtos)
        
        # --- Aba 2: Estoque ---
        if hasattr(self, 'btn_est_entrada'):
            self.btn_est_entrada.clicked.connect(lambda: self.acao_estoque("entrada"))
        if hasattr(self, 'btn_est_saida'):
            self.btn_est_saida.clicked.connect(lambda: self.acao_estoque("saida"))
        if hasattr(self, 'btn_est_consultar'):
            self.btn_est_consultar.clicked.connect(self.acao_consultar_estoque)
        if hasattr(self, 'btn_est_historico'):
            self.btn_est_historico.clicked.connect(self.acao_historico_movimentacao)
            
        # --- Aba 3: Fiscal (SUA PARTE CRÍTICA) ---
        if hasattr(self, 'btn_fisc_calcular'):
            self.btn_fisc_calcular.clicked.connect(self.acao_calcular_impostos)
        
        # NOVO: Botão para confirmar a nota (Confirm)
        if hasattr(self, 'btn_fisc_confirmar'):
            self.btn_fisc_confirmar.clicked.connect(self.acao_confirmar_nota)
            
        # --- Aba 4: Fluxo de Caixa ---
        if hasattr(self, 'btn_caixa_atualizar'):
            self.btn_caixa_atualizar.clicked.connect(self.acao_atualizar_caixa)
            
        # Atualização em tempo real ao navegar pelas abas
        if hasattr(self, 'tabWidget'):
            self.tabWidget.currentChanged.connect(self.ao_trocar_aba)

        # --- Aba 5: Nota Fiscal (MOD5) ---
        if hasattr(self, 'btn_nf_criar'):
            self.btn_nf_criar.clicked.connect(self.acao_criar_nota_fiscal)
        if hasattr(self, 'btn_nf_add_item'):
            self.btn_nf_add_item.clicked.connect(self.acao_adicionar_item_nota)
        if hasattr(self, 'btn_nf_validar_sku'):
            self.btn_nf_validar_sku.clicked.connect(self.acao_validar_sku_nota)
        if hasattr(self, 'btn_nf_totais'):
            self.btn_nf_totais.clicked.connect(self.acao_calcular_totais_nota)
        if hasattr(self, 'btn_nf_emitir'):
            self.btn_nf_emitir.clicked.connect(self.acao_emitir_nota_fiscal)

        # Chama inicialização de caixas de texto ao abrir
        self.acao_atualizar_caixa()
        self.acao_atualizar_lista_notas()
        self.acao_atualizar_dashboard()

    def ao_trocar_aba(self, idx):
        self.acao_atualizar_caixa()
        if idx == 0:  # Assumindo que o Dashboard é a aba 0
            self.acao_atualizar_dashboard()

    def acao_atualizar_dashboard(self):
        """Atualiza os indicadores na tela de Dashboard."""
        if not hasattr(self, 'lbl_dash_receitas'):
            return
            
        # 1. Indicadores Financeiros
        try:
            caixa = database.consultar_resumo_caixa()
            self.lbl_dash_receitas.setText(f"Receitas: R$ {caixa['entradas']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            self.lbl_dash_despesas.setText(f"Despesas: R$ {caixa['despesas']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            self.lbl_dash_saldo.setText(f"Saldo: R$ {caixa['saldo']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        except Exception as e:
            print(f"Erro ao carregar indicadores financeiros do dashboard: {e}")
            
        # 2. Indicadores de Estoque
        try:
            est = database.obter_indicadores_estoque()
            self.lbl_dash_total_itens.setText(f"Total em Estoque: {est['total_itens']} un.")
            self.lbl_dash_valor_est.setText(f"Valor Custo Total: R$ {est['valor_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        except Exception as e:
            print(f"Erro ao carregar indicadores de estoque do dashboard: {e}")

    def closeEvent(self, event):
        """Encerra o processo da API Flask quando a janela fecha."""
        if _api_process and _api_process.poll() is None:
            _api_process.terminate()
        event.accept()

    # --------------- MÓDULO 1: PRODUTOS ---------------
    def acao_salvar_produto(self):
        sku = self.input_sku.text().strip()
        nome = self.input_nome.text().strip()
        preco = self.input_preco.text().replace(',', '.')
        imposto = self.input_imposto.text().replace(',', '.')
        
        if not sku or not nome or not preco or not imposto:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos!")
            return
            
        try:
            sucesso, msg = database.salvar_produto(sku, nome, float(preco), float(imposto)/100)
            if sucesso:
                QMessageBox.information(self, "Sucesso", msg)
                self.input_sku.clear()
                self.input_nome.clear()
            else:
                QMessageBox.critical(self, "Erro", msg)
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Valores numéricos inválidos!")

    def acao_excluir_produto(self):
        sku = self.input_sku.text().strip()
        if not sku:
            QMessageBox.warning(self, "Aviso", "Informe o SKU para excluir!")
            return
            
        resposta = QMessageBox.question(self, "Confirmação", f"Tem certeza que deseja excluir o produto {sku} e todo o seu histórico?\nIsso afetará os relatórios passados no fluxo de caixa caso ele possua movimentações.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if resposta == QMessageBox.StandardButton.Yes:
            sucesso, msg = database.excluir_produto(sku)
            if sucesso:
                QMessageBox.information(self, "Sucesso", msg)
                self.input_sku.clear()
                self.input_nome.clear()
                self.input_preco.clear()
                self.input_imposto.clear()
                self.acao_atualizar_caixa()
            else:
                QMessageBox.critical(self, "Erro", msg)

    def acao_listar_produtos(self):
        produtos = database.listar_produtos()
        if not produtos:
            QMessageBox.information(self, "Produtos", "Nenhum produto cadastrado até o momento.")
            return
            
        texto = "=== LISTA DE PRODUTOS CADASTRADOS ===\n\n"
        for p in produtos:
            texto += f"[{p['sku']}] {p['nome']}\n"
            texto += f"   Preço Base: R$ {p['preco_base']:.2f} | Imposto: {p['aliquota']*100:.1f}%\n"
            texto += f"   Estoque Atual: {p['estoque']} unidades\n"
            texto += "-" * 40 + "\n"
            
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Reconhecimento de Produtos")
        dlg.resize(450, 400)
        
        layout = QVBoxLayout(dlg)
        
        txt = QTextEdit(dlg)
        txt.setReadOnly(True)
        txt.setPlainText(texto)
        layout.addWidget(txt)
        
        btn_fechar = QPushButton("Fechar", dlg)
        btn_fechar.clicked.connect(dlg.close)
        layout.addWidget(btn_fechar)
        
        dlg.exec()

    # --------------- MÓDULO 2: ESTOQUE ---------------
    def acao_estoque(self, tipo):
        sku    = self.input_est_sku.text().strip()
        qtd    = self.input_est_qtd.value()
        motivo = self.input_est_motivo.text().strip() if hasattr(self, 'input_est_motivo') else ''
        
        if not sku or qtd <= 0:
            QMessageBox.warning(self, "Aviso", "Informe SKU e quantidade válida!")
            return

        produto = database.buscar_produto(sku)
        if not produto:
            QMessageBox.warning(self, "Aviso", f"Produto '{sku}' não encontrado! Cadastre-o primeiro.")
            return

        if tipo == "saida":
            # SAÍDA = Venda do produto → estoque DIMINUI, empresa RECEBE dinheiro
            saldo = database.consultar_saldo_estoque(sku)
            if saldo < qtd:
                QMessageBox.warning(self, "Estoque Insuficiente",
                    f"Não é possível vender {qtd} unidade(s).\n"
                    f"Estoque disponível: {saldo} unidade(s).")
                return

        elif tipo == "entrada":
            # ENTRADA = Compra do produto → estoque AUMENTA, empresa GASTA dinheiro
            custo_total = produto["preco_base"] * qtd
            confirmacao = QMessageBox.question(
                self, "Confirmar Compra",
                f"Produto: {produto['nome']}\n"
                f"Quantidade: {qtd} unidade(s)\n"
                f"Custo total: R$ {custo_total:.2f}\n\n"
                f"Confirmar entrada no estoque?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirmacao != QMessageBox.StandardButton.Yes:
                return

        sucesso, msg = database.registrar_movimentacao(sku, tipo, qtd, motivo)
        if sucesso:
            if tipo == "entrada":
                custo = produto["preco_base"] * qtd
                QMessageBox.information(self, "✅ Compra Registrada",
                    f"Entrada de {qtd}x '{produto['nome']}' registrada!\n"
                    f"Custo: R$ {custo:.2f}")
            else:
                receita = produto["preco_base"] * qtd * 1.18
                QMessageBox.information(self, "✅ Venda Registrada",
                    f"Saída de {qtd}x '{produto['nome']}' registrada!\n"
                    f"Receita: R$ {receita:.2f}")
            if hasattr(self, 'input_est_motivo'):
                self.input_est_motivo.clear()
            self.acao_atualizar_caixa()
        else:
            QMessageBox.warning(self, "Aviso", msg)

    def acao_consultar_estoque(self):
        sku = self.input_est_sku.text().strip()
        saldo = database.consultar_saldo_estoque(sku)
        QMessageBox.information(self, "Saldo", f"Produto {sku}: {saldo} unidades.")

    def acao_historico_movimentacao(self):
        """Abre janela de histórico de movimentações atualizada em tempo real."""
        dlg = QDialog(self)
        dlg.setWindowTitle("📦 Histórico de Movimentações — Tempo Real")
        dlg.resize(620, 480)
        dlg.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel  { color: #cdd6f4; font-size: 13px; }
            QTextEdit {
                background-color: #181825;
                color: #cdd6f4;
                font-family: Consolas, monospace;
                font-size: 12px;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 6px 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #74c7ec; }
        """)

        layout = QVBoxLayout(dlg)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        # Cabeçalho
        titulo = QLabel("📋 Movimentações de Estoque (atualiza a cada 3s)")
        titulo.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(titulo)

        # Área de texto
        txt = QTextEdit(dlg)
        txt.setReadOnly(True)
        layout.addWidget(txt)

        # Indicador de status
        status_label = QLabel("🟢 Ao vivo")
        status_label.setStyleSheet("color: #a6e3a1; font-size: 11px;")
        layout.addWidget(status_label)

        # Botão fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(dlg.close)
        layout.addWidget(btn_fechar)

        def _atualizar():
            """Busca as movimentações e atualiza o QTextEdit."""
            movs = database.listar_historico_movimentacoes()
            if not movs:
                txt.setPlainText("Nenhuma movimentação registrada ainda.")
                return

            linhas = []
            linhas.append(f"{'DATA/HORA':<22} {'SKU':<12} {'TIPO':<10} {'QTD':>6}  MOTIVO")
            linhas.append("─" * 72)
            for m in movs:
                tipo = m.get('tipo', '').upper()
                emoji = "🟢 ENTRADA" if tipo == "ENTRADA" else "🔴 SAÍDA  "
                data  = m.get('data_mov', '')[:19].replace('T', ' ')
                sku   = m.get('sku', '')
                qtd   = m.get('quantidade', 0)
                motivo = m.get('motivo', '') or '—'
                linhas.append(f"{data:<22} {sku:<12} {emoji}  {qtd:>4}   {motivo}")

            txt.setPlainText("\n".join(linhas))
            # Rolagem automática para o topo (movimentação mais recente)
            txt.verticalScrollBar().setValue(0)
            status_label.setText(f"🟢 Ao vivo — última atualização: {datetime.now().strftime('%H:%M:%S')}")

        # Timer de atualização em tempo real (3 segundos)
        timer = QTimer(dlg)
        timer.timeout.connect(_atualizar)
        timer.start(3000)  # ms

        _atualizar()   # primeira carga imediata
        dlg.exec()
        timer.stop()   # para o timer ao fechar

    # --------------- MÓDULO 3: FISCAL (INTEGRADO) ---------------
    
    def acao_calcular_impostos(self):
        """ Equivalente ao /invoice/intent: Calcula sem salvar """
        sku = self.input_fisc_sku.text().strip()
        qtd = self.input_fisc_qtd.value()
        
        produto = database.buscar_produto(sku)
        if not produto:
            QMessageBox.critical(self, "Erro", "SKU inválido!")
            return

        # 1. Validar Estoque antes de calcular
        saldo = database.consultar_saldo_estoque(sku)
        if saldo < qtd:
            QMessageBox.critical(self, "Sem Saldo", f"Você possui apenas {saldo} unidades em estoque!")
            return

        # Lógica de cálculo (18% imposto simulado ou vindo do banco)
        valor_bruto = produto["preco_base"] * qtd
        valor_imposto = valor_bruto * 0.18 # Ou produto["aliquota_imposto"]
        valor_final = valor_bruto + valor_imposto

        texto = (
            f"--- INTENÇÃO DE NOTA ---\n"
            f"Produto: {produto['nome']}\n"
            f"Qtd Pedida: {qtd} (De {saldo} no estoque)\n"
            f"Impostos: R$ {valor_imposto:.2f}\n"
            f"Total: R$ {valor_final:.2f}\n"
            f"Status: Rascunho (Não salvo)"
        )
        self.txt_fisc_resultado.setPlainText(texto)

    def acao_confirmar_nota(self):
        """ Equivalente ao /invoice/confirm: Transação e Baixa de Estoque """
        sku = self.input_fisc_sku.text().strip()
        qtd = self.input_fisc_qtd.value()

        # Início da lógica de transação (Simulada via database.py)
        # 1. Validar Estoque
        saldo = database.consultar_saldo_estoque(sku)
        if saldo < qtd:
            QMessageBox.critical(self, "Erro", "Estoque insuficiente para confirmar venda!")
            return

        # 2. Processo Atômico: Baixa no estoque + Salvar Nota
        try:
            # Baixa estoque
            database.registrar_movimentacao(sku, "saida", qtd)
            
            # Cálculo final
            produto = database.buscar_produto(sku)
            total = (produto["preco_base"] * qtd) * 1.18
            
            # Salva nota no banco (Você precisará criar essa função no seu database.py)
            sucesso, msg = database.salvar_nota_fiscal(sku, qtd, total)
            
            if sucesso:
                QMessageBox.information(self, "Sucesso", "Nota Confirmada e Estoque Atualizado!")
                self.acao_atualizar_caixa()
            else:
                raise Exception("Erro ao salvar nota")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Falha na transação: {str(e)}")

    # --------------- MÓDULO 4: CAIXA ---------------
    def acao_atualizar_caixa(self):
        if not hasattr(self, 'txt_caixa_saldo'):
            return
            
        dados = database.consultar_resumo_caixa()
        texto = (
            f"=== EXTRATO SQUAD FISC ===\n"
            f"Total Entradas: R$ {dados['entradas']:.2f}\n"
            f"Total Saídas / Despesas: R$ {dados['despesas']:.2f}\n"
            f"-----------------------------\n"
            f"SALdo LÍQUIDO NO CAIXA: R$ {dados['saldo']:.2f}\n"
        )
        self.txt_caixa_saldo.setPlainText(texto)

    # --------------- MÓDULO 5: NOTA FISCAL ---------------
    def acao_criar_nota_fiscal(self):
        numero = self.input_nf_numero.text().strip()
        descricao = self.input_nf_descricao.text().strip()

        if not numero or not descricao:
            QMessageBox.warning(self, "Aviso", "Preencha o Número da Nota e a Descrição!")
            return

        sucesso, nota_id, msg = database.criar_nota_fiscal(numero, descricao)
        if sucesso:
            QMessageBox.information(self, "Sucesso", f"Nota '{numero}' aberta!\nID interno: #{nota_id}")
            self.input_nf_numero.clear()
            self.input_nf_descricao.clear()
            self.acao_atualizar_lista_notas()
        else:
            # Trata erro de duplicidade de forma amigável
            if "UNIQUE" in str(msg):
                QMessageBox.critical(self, "Erro", f"Já existe uma nota com o número '{numero}'.")
            else:
                QMessageBox.critical(self, "Erro", msg)

    def acao_atualizar_lista_notas(self):
        if not hasattr(self, 'txt_nf_status'):
            return

        notas = database.listar_notas()
        if not notas:
            self.txt_nf_status.setPlainText("Nenhuma intenção de nota fiscal criada ainda.")
            return

        linhas = ["=== INTENÇÕES DE NOTA FISCAL ==="]
        for nf in notas:
            status_icon = "✅" if nf['status'] == 'emitida' else "📄"
            linhas.append(
                f"{status_icon} [{nf['status'].upper()}] Nº {nf['numero_nota']} | {nf['descricao']} | Criada em: {nf['data_criacao']}"
            )
        self.txt_nf_status.setPlainText("\n".join(linhas))

    def acao_validar_sku_nota(self):
        """Valida o SKU em relação à nota informada e exibe o resultado no label inline."""
        numero = self.input_nf_item_nota.text().strip()
        sku = self.input_nf_item_sku.text().strip()

        if not numero or not sku:
            self.label_nf_sku_status.setText("⚠️ Informe o Nº da Nota e o SKU antes de validar.")
            return

        nota = database.buscar_nota_por_numero(numero)
        if not nota:
            self.label_nf_sku_status.setText(f"❌ Nota '{numero}' não encontrada.")
            return

        valido, codigo, mensagem, _ = database.validar_sku_para_nota(nota['id'], sku)

        # Exibe o resultado no label inline com emoção de acordo com o código
        icones = {
            'OK':            mensagem,
            'NOTA_EMITIDA':  f"🔒 {mensagem}",
            'SKU_INEXISTENTE': f"❌ {mensagem}",
            'SKU_DUPLICADO': f"⚠️ {mensagem}",
        }
        self.label_nf_sku_status.setText(icones.get(codigo, mensagem))

    def acao_adicionar_item_nota(self):
        numero = self.input_nf_item_nota.text().strip()
        sku = self.input_nf_item_sku.text().strip()
        qtd = self.input_nf_item_qtd.value()

        if not numero or not sku:
            QMessageBox.warning(self, "Aviso", "Informe o Número da Nota e o SKU do produto!")
            return

        # Busca a nota pelo número
        nota = database.buscar_nota_por_numero(numero)
        if not nota:
            QMessageBox.critical(self, "Erro", f"Nota '{numero}' não encontrada. Crie a intenção primeiro.")
            return

        # --- VALIDAÇÃO CENTRALIZADA (MOD5 - Task 4) ---
        valido, codigo, mensagem, produto = database.validar_sku_para_nota(nota['id'], sku)
        self.label_nf_sku_status.setText(mensagem)  # Atualiza label inline

        if not valido:
            QMessageBox.critical(self, f"Validação [{codigo}]", mensagem)
            return

        # Calcula e insere o item (produto já veio da validação)
        sucesso, valores, msg = database.adicionar_item_nota(
            nota['id'], sku, qtd,
            produto['preco_base'], produto['aliquota']
        )

        if sucesso:
            texto_calculo = (
                f"Item adicionado à Nota {numero}:\n"
                f"  Produto: {produto['nome']} (SKU: {sku})\n"
                f"  Quantidade: {qtd} uni.\n"
                f"  Preço Unitário: R$ {produto['preco_base']:.2f}\n"
                f"  Alíquota: {produto['aliquota']*100:.1f}%\n"
                f"  Valor Bruto: R$ {valores['valor_bruto']:.2f}\n"
                f"  Imposto: R$ {valores['valor_imposto']:.2f}\n"
                f"  Total do Item: R$ {valores['valor_total']:.2f}"
            )
            QMessageBox.information(self, "Item Calculado", texto_calculo)
            self.input_nf_item_sku.clear()
            self.input_nf_item_qtd.setValue(1)
            self.label_nf_sku_status.setText("—")
            self.acao_exibir_itens_nota(numero)
        else:
            QMessageBox.critical(self, "Erro", msg)

    def acao_exibir_itens_nota(self, numero_nota=None):
        if not hasattr(self, 'txt_nf_itens'):
            return

        if numero_nota is None:
            numero_nota = self.input_nf_item_nota.text().strip()

        nota = database.buscar_nota_por_numero(numero_nota)
        if not nota:
            self.txt_nf_itens.setPlainText(f"Nota '{numero_nota}' não encontrada.")
            return

        itens = database.listar_itens_nota(nota['id'])
        if not itens:
            self.txt_nf_itens.setPlainText(f"Nenhum item adicionado à nota {numero_nota} ainda.")
            return

        linhas = [f"=== ITENS DA NOTA {numero_nota} ==="]
        for i, item in enumerate(itens, 1):
            linhas.append(
                f"[{i}] SKU: {item['sku']} | Qtd: {item['quantidade']} | "
                f"Unit: R$ {item['preco_base']:.2f} | "
                f"Bruto: R$ {item['valor_bruto']:.2f} | "
                f"Imposto ({item['aliquota']*100:.1f}%): R$ {item['valor_imposto']:.2f} | "
                f"Total: R$ {item['valor_total']:.2f}"
            )
        self.txt_nf_itens.setPlainText("\n".join(linhas))

    def acao_calcular_totais_nota(self):
        numero = self.input_nf_item_nota.text().strip()

        if not numero:
            QMessageBox.warning(self, "Aviso", "Informe o Número da Nota no campo acima para calcular os totais!")
            return

        nota = database.buscar_nota_por_numero(numero)
        if not nota:
            QMessageBox.critical(self, "Erro", f"Nota '{numero}' não encontrada.")
            return

        totais = database.calcular_totais_nota(nota['id'])
        if not totais:
            self.txt_nf_totais.setPlainText(
                f"A nota '{numero}' ainda não possui itens.\nAdicione itens antes de calcular os totais."
            )
            return

        texto = (
            f"========================================\n"
            f"  RESUMO CONSOLIDADO — NOTA {numero}\n"
            f"  {nota['descricao']}\n"
            f"========================================\n"
            f"  Total de Itens (linhas): {totais['num_itens']}\n"
            f"  Total de Unidades:       {totais['total_qtd']}\n"
            f"----------------------------------------\n"
            f"  Total Bruto (sem imp.):  R$ {totais['total_bruto']:.2f}\n"
            f"  Total Impostos:          R$ {totais['total_imposto']:.2f}\n"
            f"========================================\n"
            f"  TOTAL FINAL DA NOTA:     R$ {totais['total_final']:.2f}\n"
            f"======================================="
        )
        self.txt_nf_totais.setPlainText(texto)

    # --------------- MOD5: EMITIR NOTA (BAIXA DE ESTOQUE) ---------------
    def acao_emitir_nota_fiscal(self):
        numero = self.input_nf_item_nota.text().strip()

        if not numero:
            QMessageBox.warning(self, "Aviso", "Informe o Número da Nota no campo acima para emitir!")
            return

        # Confirmação antes de emitir (ação irreversível)
        resposta = QMessageBox.question(
            self,
            "Confirmar Emissão",
            f"Deseja emitir a nota '{numero}'?\n\n"
            f"⚠️ Esta ação é IRREVERSÍVEL.\n"
            f"O estoque será baixado automaticamente para todos os itens da nota.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        sucesso, mensagem, relatorio = database.emitir_nota_fiscal(numero)

        if sucesso:
            linhas_relatorio = "\n".join(relatorio) if relatorio else ""
            QMessageBox.information(
                self, "✅ Nota Emitida!",
                f"{mensagem}\n\nBaixas realizadas no estoque:\n{linhas_relatorio}"
            )
            # Atualiza todos os painéis relevantes
            self.acao_atualizar_lista_notas()
            self.acao_calcular_totais_nota()
            self.acao_exibir_itens_nota(numero)
        else:
            QMessageBox.critical(self, "❌ Erro na Emissão", mensagem)


# EXECUÇÃO DO APLICATIVO
if __name__ == '__main__':
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())
