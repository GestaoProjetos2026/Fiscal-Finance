import sys
import os
import json
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6 import uic

# Lógica de importação de caminhos para recursos (UI e Backend PHP)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

import database
import auth_logic # Nome sugerido para o arquivo com a lógica de JWT que você enviou

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. CARREGAMENTO DA INTERFACE E INICIALIZAÇÃO
        uic.loadUi(resource_path("tela_principal.ui"), self)
        
        database.init_db()
        auth_logic.init_db_auth()
        
        # Variáveis de Sessão (FISC-MOD6-02)
        self.token_atual = None
        self.usuario_logado = None

        # 2. CONEXÃO DE FUNCIONALIDADES
        self.conectar_eventos()
        
        # Inicia com as abas bloqueadas (FISC-MOD6-03)
        self.atualizar_estado_login(logado=False)

    def conectar_eventos(self):
        """Mapeia todos os botões da interface"""
        # --- LOGIN / LOGOUT (FISC-MOD6-01 e 04) ---
        if hasattr(self, 'btn_login'):
            self.btn_login.clicked.connect(self.acao_fazer_login)
        if hasattr(self, 'btn_logout'):
            self.btn_logout.clicked.connect(self.acao_logout)

        # --- MÓDULO 1: PRODUTOS ---
        if hasattr(self, 'btn_salvar_produto'):
            self.btn_salvar_produto.clicked.connect(self.acao_salvar_produto)

        # --- MÓDULO 2: ESTOQUE ---
        if hasattr(self, 'btn_est_entrada'):
            self.btn_est_entrada.clicked.connect(lambda: self.acao_estoque("entrada"))
        if hasattr(self, 'btn_est_saida'):
            self.btn_est_saida.clicked.connect(lambda: self.acao_estoque("saida"))
        if hasattr(self, 'btn_est_consultar'):
            self.btn_est_consultar.clicked.connect(self.acao_consultar_estoque)

        # --- MÓDULO 3: FISCAL ---
        if hasattr(self, 'btn_fisc_calcular'):
            self.btn_fisc_calcular.clicked.connect(self.acao_calcular_impostos)

        # --- MÓDULO 4: FLUXO DE CAIXA ---
        if hasattr(self, 'btn_caixa_atualizar'):
            self.btn_caixa_atualizar.clicked.connect(self.acao_atualizar_caixa)

    # =============== LÓGICA DE SEGURANÇA (FISC-MOD6) ===============

    def acao_fazer_login(self):
        """Integração com backend de autenticação"""
        email = self.input_login_email.text().strip()
        senha = self.input_login_senha.text().strip()

        resultado = auth_logic.endpoint_login(email, senha)

        if resultado["status"] == "success":
            self.token_atual = resultado["token"]
            self.usuario_logado = auth_logic.endpoint_me(self.token_atual)
            
            QMessageBox.information(self, "Sucesso", "Login realizado com sucesso!")
            self.atualizar_estado_login(logado=True)
            self.acao_atualizar_caixa()
        else:
            QMessageBox.critical(self, "Erro", "Credenciais inválidas.")

    def acao_logout(self):
        """Encerramento de sessão e limpeza de token"""
        self.token_atual = None
        self.usuario_logado = None
        self.input_login_senha.clear()
        self.atualizar_estado_login(logado=False)
        QMessageBox.information(self, "Sessão", "Você saiu do sistema.")

    def atualizar_estado_login(self, logado):
        """Proteção de Rotas: Habilita/Desabilita abas baseado no JWT"""
        if hasattr(self, 'tabWidget'):
            # Aba 0 é o Login, as outras (1 em diante) são os módulos protegidos
            for i in range(1, self.tabWidget.count()):
                self.tabWidget.setTabEnabled(i, logado)
            
            if not logado:
                self.tabWidget.setCurrentIndex(0)

    def verificar_autorizacao(self):
        """Middleware simples de proteção"""
        if not self.token_atual:
            QMessageBox.warning(self, "Acesso Negado", "Acesso restrito. Por favor, faça login.")
            return False
        return True

    # =============== MÓDULOS DE NEGÓCIO (PRODUTOS, ESTOQUE, FISCAL) ===============

    def acao_salvar_produto(self):
        if not self.verificar_autorizacao(): return
        
        sku = self.input_sku.text().strip()
        nome = self.input_nome.text().strip()
        preco = self.input_preco.text().replace(',', '.')
        imposto = self.input_imposto.text().replace(',', '.')

        if not sku or not nome or not preco or not imposto:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos do Produto!")
            return

        try:
            preco = float(preco)
            imposto = float(imposto) / 100
            sucesso, msg = database.salvar_produto(sku, nome, preco, imposto)
            if sucesso:
                QMessageBox.information(self, "Sucesso", msg)
                self.input_sku.clear()
                self.input_nome.clear()
                self.input_preco.clear()
                self.input_imposto.clear()
            else:
                QMessageBox.critical(self, "Erro", msg)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores de preço/imposto inválidos.")

    def acao_estoque(self, tipo):
        if not self.verificar_autorizacao(): return
        
        sku = self.input_est_sku.text().strip()
        qtd = self.input_est_qtd.value()

        if not sku or qtd <= 0:
            QMessageBox.warning(self, "Aviso", "Informe SKU e quantidade válida!")
            return

        if tipo == "saida":
            saldo = database.consultar_saldo_estoque(sku)
            if saldo < qtd:
                QMessageBox.warning(self, "Erro", f"Estoque insuficiente. Saldo: {saldo}")
                return

        sucesso, msg = database.registrar_movimentacao(sku, tipo, qtd)
        if sucesso:
            QMessageBox.information(self, "Estoque", msg)
            self.input_est_sku.clear()
            self.input_est_qtd.setValue(0)
        else:
            QMessageBox.warning(self, "Erro", msg)

    def acao_consultar_estoque(self):
        if not self.verificar_autorizacao(): return
        sku = self.input_est_sku.text().strip()
        if not sku: return
        saldo = database.consultar_saldo_estoque(sku)
        QMessageBox.information(self, "Saldo", f"O produto {sku} possui {saldo} unidades.")

    def acao_calcular_impostos(self):
        if not self.verificar_autorizacao(): return
        
        sku = self.input_fisc_sku.text().strip()
        qtd = self.input_fisc_qtd.value()

        produto = database.buscar_produto(sku)
        if not produto:
            QMessageBox.critical(self, "Erro", "SKU não encontrado!")
            return

        # Preparação do JSON para o Backend PHP
        dados_intent = {
            "action": "calcular_nota",
            "items": [{"sku": sku, "preco_base": produto["preco_base"], "aliquota": produto["aliquota"], "quantidade": qtd}]
        }

        try:
            json_str = json.dumps(dados_intent)
            resultado = subprocess.run(["php", resource_path("backend_calculos.php"), json_str], capture_output=True, text=True, encoding='utf-8')
            
            if resultado.returncode == 0:
                resp = json.loads(resultado.stdout)
                if resp.get("status") == "success":
                    d = resp["data"]
                    self.txt_fisc_resultado.setPlainText(f"TOTAL BRUTO: R$ {d['total_bruto']}\nIMPOSTO: R$ {d['total_imposto']}\nFINAL: R$ {d['total_final']}")
            else:
                self.txt_fisc_resultado.setPlainText("Erro no backend PHP.")
        except Exception as e:
            self.txt_fisc_resultado.setPlainText(f"Erro de integração: {str(e)}")

    def acao_atualizar_caixa(self):
        if not self.token_atual: return
        
        dados = database.consultar_resumo_caixa()
        texto = (
            f"=== FLUXO DE CAIXA (AUTENTICADO) ===\n"
            f"Entradas: R$ {dados['entradas']:.2f}\n"
            f"Saídas: R$ {dados['despesas']:.2f}\n"
            f"-----------------------------\n"
            f"SALDO ATUAL: R$ {dados['saldo']:.2f}\n"
        )
        self.txt_caixa_saldo.setPlainText(texto)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())
