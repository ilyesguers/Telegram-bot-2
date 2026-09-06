"""مشغّل كل الاختبارات دفعة واحدة.

كل مجموعة تعمل في عملية مستقلة لأنها تهيّئ بيئة (قاعدة بيانات/مجلد) خاصة بها.

    python tests/run_all.py
"""

import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SUITES = [
    "test_channel_broadcasting.py",
    "test_smoke_flows.py",
    "test_resilience.py",
]


def main():
    failures = []
    for suite in SUITES:
        path = TESTS_DIR / suite
        print(f"\n{'=' * 60}\n▶️  {suite}\n{'=' * 60}")
        result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
        output = (result.stdout or "") + (result.stderr or "")
        summary = [line for line in output.splitlines()
                   if line.startswith(("Ran ", "OK", "FAILED"))]
        print("\n".join(summary) or output[-800:])
        if result.returncode != 0:
            failures.append(suite)
            print(output[-2500:])

    print(f"\n{'=' * 60}")
    if failures:
        print(f"❌ مجموعات فاشلة: {', '.join(failures)}")
        return 1
    print("✅ كل مجموعات الاختبار ناجحة")
    return 0


if __name__ == "__main__":
    sys.exit(main())
