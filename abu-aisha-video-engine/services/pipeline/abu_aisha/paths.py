"""Repository-relative locations (overridable through environment variables)."""
from __future__ import annotations

import os
from pathlib import Path

ENGINE_ROOT = Path(os.environ.get("ABU_AISHA_ROOT", Path(__file__).resolve().parents[3]))
PACKAGES = ENGINE_ROOT / "packages"
FONTS_DIR = PACKAGES / "brand" / "fonts"
BRAND_ASSETS = PACKAGES / "brand" / "assets"
PROMPTS_DIR = PACKAGES / "prompts"
SCHEMA_DIR = PACKAGES / "schema"
RENDERER_DIR = ENGINE_ROOT / "apps" / "renderer"
PROJECTS_DIR = Path(os.environ.get("ABU_AISHA_PROJECTS", ENGINE_ROOT / "data" / "projects"))
