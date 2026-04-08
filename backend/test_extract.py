import httpx

r = httpx.get(
    "http://localhost:8000/api/documents/extracted-details",
    headers={"X-User-Email": "sarthiksunil666@gmail.com"},
)
data = r.json()
print("=== Extracted Details ===")
print(f"Documents count: {data.get('documents_count')}")
print(f"Patient Name:    {data.get('patient_name', '(empty)')}")
print(f"Insurer Name:    {data.get('insurer_name', '(empty)')}")
print(f"Claim Amount:    {data.get('claim_amount', '(empty)')}")
print(f"Denial Reason:   {data.get('denial_reason', '(empty)')}")
print(f"Policy Number:   {data.get('policy_number', '(empty)')}")
print(f"Hospital:        {data.get('hospital', '(empty)')}")
print(f"Diagnosis:       {data.get('diagnosis', '(empty)')}")
print(f"Sources:         {data.get('extraction_sources', {})}")
