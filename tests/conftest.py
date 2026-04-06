"""Shared constants and utilities for ekline-docs-skills tests."""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SKILLS_DIR = os.path.join(PROJECT_ROOT, "skills")
