import requests
import unittest

BASE_URL = "http://localhost:5000/v1/fisc"

class TestModulo3(unittest.TestCase):
    # FISC-MOD3-02 — Testes de segurança (Auth e RBAC)
    def test_protecao_jwt_obrigatoria(self):
        # Tenta acessar rota protegida sem token
        res = requests.get(f"{BASE_URL}/auth/me")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["message"], "Não autorizado. Faça login e use o header Authorization: Bearer <token>.")

    # FISC-MOD3-03 — Testes de regressão pós-integração (Fluxo de Caixa)
    def test_regressao_saldo_caixa(self):
        # Valida se o saldo atualizado em 30/04 usa a tabela 'caixa' como fonte única
        res = requests.get(f"{BASE_URL}/cashflow/balance")
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        # Garante que o campo 'saldo_liquido' existe e é calculado corretamente
        self.assertTrue("saldo_liquido" in data)
        self.assertEqual(data["saldo_liquido"], data["total_entradas"] - data["total_despesas"])

if __name__ == "__main__":
    unittest.main()
