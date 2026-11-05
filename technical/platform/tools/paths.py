"""Every folder location in the library, in one place. Tools and tests import from here."""

from pathlib import Path

PLATFORM = Path(__file__).resolve().parent.parent
TECHNICAL = PLATFORM.parent
ROOT = TECHNICAL.parent

# Company-wide
GLOSSARY = ROOT / "GLOSSARY.md"
ROLES = ROOT / "roles-and-lifecycle"
BEST_PRACTICES = ROOT / "best-practices"

# Non-technical track (Microsoft Copilot)
NON_TECHNICAL = ROOT / "non-technical"
SHARED = NON_TECHNICAL / "shared"
PREAMBLE = SHARED / "laya-preamble.md"
PII_GUARD = SHARED / "pii-guard.md"
# Licence tiers. "everyone" works on free Copilot Chat; "paid-licence" needs the Microsoft Copilot licence.
TIERS = {"everyone": NON_TECHNICAL / "everyone", "paid-licence": NON_TECHNICAL / "paid-licence"}
SKILLS = TIERS["everyone"] / "skills"
AGENTS = TIERS["everyone"] / "agents"
PAID_SKILLS = TIERS["paid-licence"] / "skills"
PAID_AGENTS = TIERS["paid-licence"] / "agents"
PACKAGE_SETTINGS = NON_TECHNICAL / "package.yaml"
TEMPLATES = NON_TECHNICAL / "templates"
TEMPLATE_WORKBOOKS = TEMPLATES / "workbooks"
TEMPLATE_DOCUMENTS = TEMPLATES / "documents"
STAFF_GUIDE = NON_TECHNICAL / "staff-guide"
STAFF_GUIDE_PAGES = STAFF_GUIDE / "agents"
ADMIN = NON_TECHNICAL / "admin"
READY = NON_TECHNICAL / "ready-to-use"
READY_AGENTS = READY / "agents"
READY_TEMPLATES = READY / "templates"
STAFF_GUIDE_DOCX = READY / "Laya-AI-Agents-Staff-Guide.docx"
BY_ROLE = NON_TECHNICAL / "by-role"
PROMPTS = NON_TECHNICAL / "prompts"
TRAINING = NON_TECHNICAL / "training"

# Technical track (GitHub Copilot)
SKILLS_AND_AGENTS = TECHNICAL / "skills-and-agents"
DEV_SKILLS = SKILLS_AND_AGENTS / "skills"
DEV_AGENTS = SKILLS_AND_AGENTS / "agents"
HARNESS = TECHNICAL / "harness"
REPO_KIT = HARNESS / "repo-kit"
SRC = PLATFORM / "src"
BACKEND = PLATFORM / "backend"
TOOLS = PLATFORM / "tools"
TESTS = PLATFORM / "tests"
CATALOG = PLATFORM / "catalog.yaml"
BUILD = PLATFORM / "build"
