import requests
import unittest

BASE_URL = "http://localhost:5000/v1/fisc"

class TestQualidadeS4(unittest.TestCase):
    def setUp(self):
        login = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@fiscal.com", "senha": "admin123"})
        self.headers = {"Authorization": login.json()["data"]["token"]}

    # FISC-MOD3-01 — Testes integração módulos core
    def test_core_communication(self):
        res = requests.get(f"{BASE_URL}/products", headers=self.headers)
        self.assertEqual(res.status_code, 200)

    # FISC-MOD3-02 — Testes de segurança (auth e permissões)
    def test_security_access(self):
        res = requests.get(f"{BASE_URL}/auth/me") # Sem headers
        self.assertEqual(res.status_code, 401)

    # FISC-MOD3-03 — Testes de regressão pós-integração
    def test_regression_rules(self):
        data = {"sku": "REG-TEST", "nome": "T", "preco_base": 1, "aliquota_imposto": 0.1}
        requests.post(f"{BASE_URL}/products", json=data, headers=self.headers)
        res = requests.post(f"{BASE_URL}/products", json=data, headers=self.headers)
        self.assertEqual(res.status_code, 409) # SKU deve continuar sendo único

if __name__ == "__main__":
    unittest.main()
