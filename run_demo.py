import json
import sys

from vision.pipeline import analyze


def main():
    address = " ".join(sys.argv[1:]) or "1 Yonge St, Toronto, ON"
    result = analyze(address)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
