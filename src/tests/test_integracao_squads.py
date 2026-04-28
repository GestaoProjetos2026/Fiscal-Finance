import requests
import unittest

BASE_URL = "http://localhost:5000/v1/fisc"

class TestIntegracaoS4(unittest.TestCase):
    # FISC-MOD1-01 — Teste de integração com Auth (Squad 1)
    def test_auth_squad1(self):
        res = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@fiscal.com", "senha": "admin123"})
        self.assertEqual(res.status_code, 200)

    # FISC-MOD1-04 — Teste end-to-end do ERP completo
    def test_erp_full_flow(self):
        login = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@fiscal.com", "senha": "admin123"})
        headers = {"Authorization": login.json()["data"]["token"]}
        venda = {"numero": "NF-S4-E2E", "itens": [{"sku": "PROD-001", "quantidade": 1}]}
        res = requests.post(f"{BASE_URL}/invoice/confirm", json=venda, headers=headers)
        self.assertIn(res.status_code, [201, 409])

if __name__ == "__main__":
    unittest.main()
