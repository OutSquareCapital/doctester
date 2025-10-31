import sys
from pathlib import Path


def main() -> None:
    print("--- Running internal doctester test ---")

    project_root = Path(__file__).parent.parent
    src_dir = project_root.joinpath("src")

    if not src_dir.is_dir():
        print(f"Error: src/ directory not found at {src_dir}")
        sys.exit(1)

    sys.path.insert(0, str(src_dir))

    try:
        from doctester import run_on_file
    except ImportError:
        print(f"Failed to import doctester from {src_dir}")
        print(f"sys.path: {sys.path}")
        sys.exit(1)

    pyi_file = Path(__file__).parent.joinpath("foo.pyi")
    if not pyi_file.exists():
        print(f"Test file not found: {pyi_file}")
        sys.exit(1)

    print(f"Testing against: {pyi_file.name}")

    try:
        run_on_file(pyi_file, verbose=True)
        print("--- Internal test PASSED (if no errors above) ---")
    except SystemExit as e:
        if e.code == 0:
            print("--- Internal test PASSED (SystemExit code 0) ---")
        else:
            print(f"--- Internal test FAILED (SystemExit: {e.code}) ---")
            sys.exit(e.code)
    except Exception as e:
        print(f"--- Internal test FAILED (Exception: {e}) ---")
        sys.exit(1)


if __name__ == "__main__":
    main()
