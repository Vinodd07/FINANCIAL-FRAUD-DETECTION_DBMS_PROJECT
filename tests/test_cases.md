# Test Cases

| Test ID | Test Scenario | Expected Result | Observed Result |
|---|---|---|---|
| TC-01 | FastAPI to Neo4j connection | Backend connects successfully | PASS |
| TC-02 | Valid customer login | Customer dashboard appears | PASS |
| TC-03 | Staff login for each role | Role-specific dashboard appears | PASS |
| TC-04 | View owned account | Correct account information appears | PASS |
| TC-05 | Register beneficiary | Beneficiary is stored | PASS |
| TC-06 | Low-risk demo transfer | SUCCESS path | PASS |
| TC-07 | Medium-risk demo transfer | Simulated OTP path | PASS |
| TC-08 | High-risk demo transfer | BLOCKED path | PASS |
| TC-09 | Inspect transaction risk factors | Fraud factors are visible | PASS |
| TC-10 | Raise support ticket | Customer is linked to ticket | PASS |
| TC-11 | Run Cypher queries | Expected graph records appear | PASS |
