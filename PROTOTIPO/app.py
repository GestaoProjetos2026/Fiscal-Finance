import sys
import os
import json
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6 import uic

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

import database

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. CARREGA O NOVO DESENHO DA TELA (.ui)
        uic.loadUi(resource_path("tela_principal.ui"), self)
        
        # Inicia o SQLite com as tabelas
        database.init_db()
        
        # 2. CONECTA FUNCIONALIDADES AOS BOTÕES
        
        # --- Aba 1: Produtos ---
        if hasattr(self, 'btn_salvar_produto'):
            self.btn_salvar_produto.clicked.connect(self.acao_salvar_produto)
        
        # --- Aba 2: Estoque ---
        if hasattr(self, 'btn_est_entrada'):
            self.btn_est_entrada.clicked.connect(lambda: self.acao_estoque("entrada"))
        if hasattr(self, 'btn_est_saida'):
            self.btn_est_saida.clicked.connect(lambda: self.acao_estoque("saida"))
        if hasattr(self, 'btn_est_consultar'):
            self.btn_est_consultar.clicked.connect(self.acao_consultar_estoque)
            
        # --- Aba 3: Fiscal ---
        if hasattr(self, 'btn_fisc_calcular'):
            self.btn_fisc_calcular.clicked.connect(self.acao_calcular_impostos)
            
        # --- Aba 4: Fluxo de Caixa ---
        if hasattr(self, 'btn_caixa_atualizar'):
            self.btn_caixa_atualizar.clicked.connect(self.acao_atualizar_caixa)

        # Chama inicialização de caixas de texto ao abrir
        self.acao_atualizar_caixa()

    # --------------- MÓDULO 1: PRODUTOS ---------------
    def acao_salvar_produto(self):
        sku = self.input_sku.text().strip()
        nome = self.input_nome.text().strip()
        preco = self.input_preco.text().replace(',', '.')
        imposto = self.input_imposto.text().replace(',', '.')
        
        if not sku or not nome or not preco or not imposto:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos do Produto!")
            return
            
        try:
            preco = float(preco)
            imposto = float(imposto) / 100 # Se digitar 12 (%), vira 0.12
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Preço e Imposto devem ser valores numéricos!")
            return
            
        sucesso, msg = database.salvar_produto(sku, nome, preco, imposto)
        if sucesso:
            QMessageBox.information(self, "Sucesso", msg)
            self.input_sku.clear()
            self.input_nome.clear()
            self.input_preco.clear()
            self.input_imposto.clear()
        else:
            QMessageBox.critical(self, "Erro", msg)

    # --------------- MÓDULO 2: ESTOQUE ---------------
    def acao_estoque(self, tipo):
        sku = self.input_est_sku.text().strip()
        qtd = self.input_est_qtd.value()
        
        if not sku:
            QMessageBox.warning(self, "Aviso", "Informe o SKU para lançar no estoque!")
            return
            
        if qtd <= 0:
            QMessageBox.warning(self, "Aviso", "Informe uma quantidade maior que zero!")
            return
            
        if tipo == "saida":
            saldo_atual = database.consultar_saldo_estoque(sku)
            if saldo_atual < qtd:
                QMessageBox.warning(self, "Sem Saldo", f"Saldo Insuficiente. Saldo Atual: {saldo_atual}.")
                return
                
        sucesso, msg = database.registrar_movimentacao(sku, tipo, qtd)
        if sucesso:
            QMessageBox.information(self, "Estoque", msg)
            self.input_est_sku.clear()
            self.input_est_qtd.setValue(0)
        else:
            QMessageBox.warning(self, "Aviso", msg)

    def acao_consultar_estoque(self):
        sku = self.input_est_sku.text().strip()
        if not sku:
            QMessageBox.warning(self, "Aviso", "Informe o SKU!")
            return
            
        saldo = database.consultar_saldo_estoque(sku)
        QMessageBox.information(self, "Saldo de Estoque", f"O produto {sku} tem {saldo} unidades em estoque.")

    # --------------- MÓDULO 3: FISCAL (CÁLCULO PHP) ---------------
    def acao_calcular_impostos(self):
        sku = self.input_fisc_sku.text().strip()
        qtd = self.input_fisc_qtd.value()
        
        if not sku or qtd <= 0:
            QMessageBox.warning(self, "Aviso", "Informe o SKU e a quantidade para calcular a nota.")
            return
            
        produto = database.buscar_produto(sku)
        if not produto:
            QMessageBox.critical(self, "Erro", f"Produto com SKU '{sku}' não consta na base de dados (MOD1).")
            return
            
        # Preparar o JSON para enviar ao PHP
        dados_intent = {
            "action": "calcular_nota",
            "items": [
                {
                    "sku": produto["sku"],
                    "preco_base": produto["preco_base"],
                    "aliquota": produto["aliquota"],
                    "quantidade": qtd
                }
            ]
        }
        
        json_str = json.dumps(dados_intent)
        
        # 3. INTERAÇÃO EXTERNA (API / PHP)
        # Executa o PHP via command line, simulando um backend REST com resposta JSON
        try:
            # Requer que 'php' esteja instalado e adicionado nas variáveis de ambiente.
            resultado = subprocess.run(["php", resource_path("backend_calculos.php"), json_str], capture_output=True, text=True, encoding='utf-8')
            
            if resultado.returncode != 0:
                self.txt_fisc_resultado.setPlainText(f"Erro ao chamar o backend PHP: {resultado.stderr}")
                return
                
            resposta_api = json.loads(resultado.stdout)
            
            if resposta_api.get("status") == "success":
                data = resposta_api["data"]
                texto_formatado = (
                    f"--- INTEÇÃO DE NOTA FISCAL ---\n"
                    f"Produto: {produto['nome']} ({qtd} uni.)\n"
                    f"Valor Bruto: R$ {data['total_bruto']}\n"
                    f"Valor Imposto: R$ {data['total_imposto']}\n"
                    f"-------------------------------\n"
                    f"VALOR FINAL: R$ {data['total_final']}\n\n"
                    f"(Retornado pelo PHP 🐘)"
                )
                self.txt_fisc_resultado.setPlainText(texto_formatado)
            else:
                 self.txt_fisc_resultado.setPlainText(f"Erro reportado via PHP: {resposta_api.get('message')}")
                 
        except FileNotFoundError:
             # Fallback: Cálculos via Python caso o PHP não esteja instalado.
             preco_base = float(produto['preco_base'])
             aliquota = float(produto['aliquota'])
             quantidade = float(qtd)
             
             imposto_item = preco_base * aliquota * quantidade
             total_item = (preco_base * quantidade) + imposto_item
             total_bruto = preco_base * quantidade
             
             texto_formatado = (
                 f"--- INTEÇÃO DE NOTA FISCAL (Modo Python Fallback) ---\n"
                 f"Produto: {produto['nome']} ({qtd} uni.)\n"
                 f"Valor Bruto: R$ {total_bruto:.2f}\n"
                 f"Valor Imposto: R$ {imposto_item:.2f}\n"
                 f"-------------------------------\n"
                 f"VALOR FINAL: R$ {total_item:.2f}\n\n"
                 f"(Aviso: PHP não encontrado. Cálculo executado via Python 🐍)"
             )
             self.txt_fisc_resultado.setPlainText(texto_formatado)
        except Exception as e:
            self.txt_fisc_resultado.setPlainText(f"Ocorreu um erro na requisição: {str(e)}")

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())
