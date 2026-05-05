import requests
import unittest

BASE_URL = "http://localhost:5000/v1"

class TestModulo1(unittest.TestCase):
    # FISC-MOD1-01 — Teste de integração com Auth (Squad 1)
    def test_integracao_auth_squad1(self):
        payload = {"email": "admin@fiscal.com", "senha": "admin123"}
        res = requests.post(f"{BASE_URL}/fisc/auth/login", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertIn("token", res.json()["data"])

    # FISC-MOD1-04 — Teste end-to-end do fluxo completo
    def test_fluxo_e2e_fiscal(self):
        # Simula consulta de estoque via API Pública (X-API-KEY)
        headers = {"X-API-KEY": "FISC-PUBLIC-2026-SQUAD4"}
        res = requests.get(f"{BASE_URL}/public/fisc/stock/PROD-001", headers=headers)
        self.assertIn(res.status_code, [200, 404])

if __name__ == "__main__":
    unittest.main()
