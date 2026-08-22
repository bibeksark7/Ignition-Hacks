import json
import sys

from vision.cache import analyze_cached


def main():
    address = " ".join(a for a in sys.argv[1:] if a != "--fresh") or "1 Yonge St, Toronto, ON"
    force_refresh = "--fresh" in sys.argv
    result = analyze_cached(address, force_refresh=force_refresh)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
