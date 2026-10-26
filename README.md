# AI Business Automation — LeadPilot AI

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Passing](https://img.shields.io/badge/Tests-48%2F48_Passed-brightgreen.svg)](leadpilot-ai/services/ai/tests)

An enterprise-ready, production-grade AI business automation software suite acting as a virtual AI operations team. Built for mid-market service businesses (featuring **BrightSmile Dental** as a reference demo tenant).

---

## 🚀 Quick Navigation

- **[LeadPilot AI Application & Architecture](leadpilot-ai/README.md)**: Full architecture breakdown, hiring matrix, and quickstart guide.
- **[System Architecture](leadpilot-ai/docs/ARCHITECTURE.md)**: Multi-agent state machines, hybrid vector RAG, and schema design.
- **[Client & Upwork Q&A](leadpilot-ai/docs/UPWORK_ANSWERS.md)**: Enterprise hiring answers grounded directly in this repository's codebase.
- **[Demo Walkthrough Script](leadpilot-ai/docs/DEMO_SCRIPT.md)**: 10-minute guided client presentation.
- **[OpenAPI & REST Reference](leadpilot-ai/docs/API.md)**: Complete endpoint documentation.

---

## ⚡ 5-Minute Local Launch

```bash
# 1. Enter the application directory
cd leadpilot-ai

# 2. Copy the environment configuration
cp .env.example .env

# 3. Run the automated test suite (48 tests in ~2.5s)
python -m pytest services/ai/tests services/mcp/test_mcp.py -v

# 4. Run end-to-end simulation across 8 business workflows
python scripts/simulate_all.py

# 5. Start the web management dashboard
cd web
npm install
npm run dev
# Open http://localhost:3000
```
