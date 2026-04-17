import sys
import os
import json
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6 import uic
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
            self.tabWidget.currentChanged.connect(lambda idx: self.acao_atualizar_caixa())

        self.acao_atualizar_caixa()

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
        sku = self.input_est_sku.text().strip()
        qtd = self.input_est_qtd.value()
        
        if not sku or qtd <= 0:
            QMessageBox.warning(self, "Aviso", "Informe SKU e quantidade válida!")
            return
            
        if tipo == "saida":
            saldo = database.consultar_saldo_estoque(sku)
            if saldo < qtd:
                QMessageBox.warning(self, "Sem Saldo", f"Saldo insuficiente: {saldo}")
                return
        elif tipo == "entrada":
            produto = database.buscar_produto(sku)
            if not produto:
                QMessageBox.warning(self, "Aviso", "Produto não encontrado!")
                return
            custo_total = produto["preco_base"] * qtd
            resumo_caixa = database.consultar_resumo_caixa()
            if resumo_caixa["saldo"] < custo_total:
                QMessageBox.warning(self, "Saldo Insuficiente", f"Fluxo de caixa insuficiente (R$ {resumo_caixa['saldo']:.2f}) para pagar esta compra (R$ {custo_total:.2f})!")
                return
                
        sucesso, msg = database.registrar_movimentacao(sku, tipo, qtd)
        if sucesso:
            QMessageBox.information(self, "Estoque", msg)
            self.acao_atualizar_caixa()
        else:
            QMessageBox.warning(self, "Aviso", msg)

    def acao_consultar_estoque(self):
        sku = self.input_est_sku.text().strip()
        saldo = database.consultar_saldo_estoque(sku)
        QMessageBox.information(self, "Saldo", f"Produto {sku}: {saldo} unidades.")

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
        if hasattr(self, 'txt_caixa_saldo'):
            dados = database.consultar_resumo_caixa()
            texto = (
                f"=== EXTRATO SQUAD FISC ===\n"
                f"Entradas: R$ {dados['entradas']:.2f}\n"
                f"Saídas: R$ {dados['despesas']:.2f}\n"
                f"SALDO ATUAL: R$ {dados['saldo']:.2f}"
            )
            self.txt_caixa_saldo.setPlainText(texto)

# EXECUÇÃO DO APLICATIVO
if __name__ == '__main__':
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())
