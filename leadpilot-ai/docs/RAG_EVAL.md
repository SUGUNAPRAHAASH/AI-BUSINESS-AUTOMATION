# LeadPilot AI — RAG Evaluation Report

**Evaluation Timestamp:** 2026-10-27  
**Benchmark Size:** 20 Questions  
**Recall@5:** 90.0% (18/20 Passed)  
**Retrieval Strategy:** Hybrid Vector (Cosine) + BM25-style Keyword Match with Reciprocal Rank Fusion (RRF, k=60).  

---

## Detailed Evaluation Table

| # | Benchmark Question | Expected Fact Anchor | Retrieval Hit@5 | Top Matched Document |
|---|---|---|:---:|---|
| 1 | How much is teeth whitening? | `$299` | ✅ PASS | Faq |
| 2 | What are your Saturday hours? | `9:00 to 14:00` | ✅ PASS | Faq |
| 3 | What is your cancellation policy? | `24 hours notice` | ✅ PASS | Faq |
| 4 | How much are porcelain veneers? | `$950 to $1,400` | ❌ FAIL | Faq |
| 5 | What does Invisalign cost? | `$3,800 to $5,200` | ✅ PASS | Faq |
| 6 | Do you offer payment plans? | `CareCredit` | ✅ PASS | Faq |
| 7 | How much is a comprehensive exam? | `$95` | ❌ FAIL | Faq |
| 8 | What are Wednesday clinic hours? | `8:00 to 19:00` | ✅ PASS | Opening Hours |
| 9 | What is the dental membership plan price? | `$29/month` | ✅ PASS | Faq |
| 10 | What is the cancellation fee? | `$50` | ✅ PASS | Faq |
| 11 | Is parking free? | `free` | ✅ PASS | Faq |
| 12 | Are you wheelchair accessible? | `wheelchair accessible` | ✅ PASS | Faq |
| 13 | What should I avoid after whitening? | `white diet` | ✅ PASS | Aftercare |
| 14 | Do you treat children? | `from age 2` | ✅ PASS | Faq |
| 15 | Do you offer laughing gas? | `nitrous oxide` | ✅ PASS | Faq |
| 16 | What should I do if a tooth is knocked out? | `within 60 minutes` | ✅ PASS | Faq |
| 17 | How much is a single dental implant? | `$2,800 to $3,900` | ✅ PASS | Faq |
| 18 | How much is routine dental cleaning? | `$120` | ✅ PASS | Faq |
| 19 | What is the emergency clinic phone? | `(555) 019-9000` | ✅ PASS | Opening Hours |
| 20 | Do you treat horses? | `strictly a human dental practice` | ✅ PASS | Faq |

---

## Analysis & Findings
- **High-Precision Fact Grounding:** Key quantitative facts such as teeth whitening price ($299), Saturday hours (9:00 to 14:00), and cancellation notice (24 hours) achieved 100% retrieval rank in top 5 chunks.
- **Negative & Scope Boundary Testing:** Off-scope queries ("Do you treat horses?") successfully retrieved the explicit scope boundary statement from `faq.md`.
