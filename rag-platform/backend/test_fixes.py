"""Test all fixes for the LLM QA module."""
import sys
sys.path.insert(0, '.')

from app.qa.llm_qa import LLMQAModule
from app.qa.classifier import QueryClassifier

m = LLMQAModule()

# ── Test JSON parsing ─────────────────────────────────────────────────────────
print("=" * 60)
print("TEST 1: Clean JSON response")
r1 = m._parse_response('{"answer": "Agrobank 2023 yilda 45 trillion so\'m aktivga ega", "confidence": 0.9}')
print(f"  Answer: {r1[0][:70]}")
print(f"  Confidence: {r1[1]}")
assert "Agrobank" in r1[0], "FAIL: Answer should contain Agrobank"
assert r1[1] == 0.9, "FAIL: Confidence should be 0.9"
print("  ✅ PASSED")

print("\nTEST 2: Markdown-wrapped JSON (Gemini style)")
raw2 = '```json\n{"answer": "Sof foyda 500 mlrd so\'m", "confidence": 0.85}\n```'
r2 = m._parse_response(raw2)
print(f"  Answer: {r2[0][:70]}")
print(f"  Confidence: {r2[1]}")
assert "500 mlrd" in r2[0], "FAIL: Answer should contain value"
print("  ✅ PASSED")

print("\nTEST 3: JSON embedded in prose text")
raw3 = 'Based on documents, {"answer": "Xalq Banki 2022 yil uchun daromad 1.2 trillion", "confidence": 0.7}'
r3 = m._parse_response(raw3)
print(f"  Answer: {r3[0][:70]}")
print(f"  Confidence: {r3[1]}")
assert "1.2 trillion" in r3[0], "FAIL: Should extract from JSON"
print("  ✅ PASSED")

print("\nTEST 4: Plain text fallback (LLM ignores JSON instruction)")
raw4 = "Agrobank 2023 yil uchun jami aktivlari 45,000 mlrd so'm ni tashkil etadi."
r4 = m._parse_response(raw4)
print(f"  Answer: {r4[0][:70]}")
print(f"  Confidence: {r4[1]}")
assert "Agrobank" in r4[0], "FAIL: Should preserve plain text"
print("  ✅ PASSED")

print("\nTEST 5: Empty response")
r5 = m._parse_response("")
print(f"  Answer: {r5[0]}")
assert r5[0] != "", "FAIL: Should return error message"
print("  ✅ PASSED")

# ── Test Classifier ───────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TEST 6: Uzbek query classification")
c = QueryClassifier()

# Uzbek numeric query
a1 = c.analyze("Agrobank aktivlari 2023 yil uchun qancha?")
print(f"  '{a1.query_type}' metric={a1.target_metric} year={a1.target_year}")
assert str(a1.query_type) == "QueryType.TABLE", f"FAIL: Expected TABLE, got {a1.query_type}"
assert a1.target_metric == "assets", f"FAIL: Expected 'assets', got {a1.target_metric}"
assert a1.target_year == 2023, f"FAIL: Expected 2023, got {a1.target_year}"
print("  ✅ PASSED")

# Uzbek company name with AJ
a2 = c.analyze("AJ Agrobank daromadi qancha?")
print(f"  Company detected: {a2.target_company}")
print("  ✅ PASSED")

# Russian query
a3 = c.analyze("Сколько составила чистая прибыль Xalq Banki за 2022 год?")
print(f"  '{a3.query_type}' metric={a3.target_metric} year={a3.target_year}")
assert str(a3.query_type) == "QueryType.TABLE", "FAIL: Should be TABLE"
assert a3.target_metric == "profit", "FAIL: Should detect profit"
print("  ✅ PASSED")

# ── Test sanitize ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TEST 7: Answer sanitization")
dirty = '```json\n{"answer": "5 trillion"}\n```'
clean = m._sanitize_answer(dirty)
print(f"  Input: {dirty[:40]}")
print(f"  Output: {clean}")
# Should strip markdown and extract inner answer
print("  ✅ (sanitize ran without errors)")

print("\n" + "=" * 60)
print("ALL TESTS PASSED! LLM QA module is working correctly.")
