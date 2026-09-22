from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.ai.pipeline import pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Translate speech locally between English and Armenian."
    )
    parser.add_argument("input", type=Path, help="Input audio file")
    parser.add_argument("output", type=Path, help="Output WAV file")
    parser.add_argument("--source", choices=["en", "hy"], required=True)
    parser.add_argument("--target", choices=["en", "hy"], required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = pipeline.run(
        input_audio=args.input,
        output_audio=args.output,
        source_language=args.source,
        target_language=args.target,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
