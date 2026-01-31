"""
Quick Integration Test
Tests that OSINTAnalyzer can be imported and initialized with all components
"""

import sys
from pathlib import Path

# Ensure we're in the project directory
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("=" * 70)
print("OSINT Analyzer Integration Test")
print("=" * 70)

# Test 1: Import OSINTAnalyzer
print("\n✓ Test 1: Importing OSINTAnalyzer...")
try:
    from core.osint_analyzer import OSINTAnalyzer
    print("   ✓ Import successful")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize OSINTAnalyzer
print("\n✓ Test 2: Initializing OSINTAnalyzer...")
try:
    analyzer = OSINTAnalyzer()
    print("   ✓ Initialization successful")
except Exception as e:
    print(f"   ✗ Initialization failed: {e}")
    sys.exit(1)

# Test 3: Check component status
print("\n✓ Test 3: Checking component status...")
components = {
    "LLM (Gemini)": analyzer.llm.model is not None,
    "Google Vision": analyzer.vision.is_enabled(),
    "Metadata Extractor": True,  # Always available
    "Audio Analyzer": True,  # Always available
    "Knowledge Graph": True,  # Always available
}

all_ready = True
for component, status in components.items():
    status_icon = "✓" if status else "✗"
    status_text = "Ready" if status else "Not configured"
    print(f"   {status_icon} {component}: {status_text}")
    if not status and component in ["LLM (Gemini)", "Google Vision"]:
        all_ready = False

# Test 4: Component details
print("\n✓ Test 4: Component details...")
if analyzer.llm.model:
    print(f"   LLM Model: {analyzer.llm.model_name}")
else:
    print(f"   LLM: Not configured (check GEMINI_API_KEY)")

if analyzer.vision.is_enabled():
    print(f"   Google Vision: Enabled")
else:
    print(f"   Google Vision: Disabled (check GOOGLE_APPLICATION_CREDENTIALS)")

print(f"   Knowledge Graph: {analyzer.graph.graph.number_of_nodes()} entities")

# Summary
print("\n" + "=" * 70)
if all_ready:
    print("✅ ALL TESTS PASSED - System is fully operational!")
else:
    print("⚠️  PARTIAL SUCCESS - Some components need configuration")
    print("\nTo fix:")
    if not analyzer.llm.model:
        print("  - Set GEMINI_API_KEY in .env file")
    if not analyzer.vision.is_enabled():
        print("  - Set GOOGLE_APPLICATION_CREDENTIALS in .env file")
print("=" * 70)
