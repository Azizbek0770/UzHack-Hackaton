from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

try:
    import fitz  # type: ignore
except Exception:
    fitz = None


def _write_pdf(path: Path, text_pages: list[str]) -> None:
    if fitz is None:
        return
    document = fitz.open()
    for text in text_pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()


def run() -> None:
    output_root = Path(__file__).resolve().parents[2] / "upload_examples"
    output_root.mkdir(parents=True, exist_ok=True)

    alpha_dir = output_root / "AlphaBank"
    alpha_dir.mkdir(parents=True, exist_ok=True)
    _write_pdf(
        alpha_dir / "alpha_management_ru.pdf",
        [
            "Отчет AlphaBank за 2024 год. Стратегия роста и контроль рисков.",
            "Выручка и прибыль улучшились благодаря цифровизации.",
        ],
    )
    pd.DataFrame(
        {"Metric": ["Revenue", "Profit", "Assets"], "2023": [1200, 230, 3100], "2024": [1450, 290, 3550]}
    ).to_excel(alpha_dir / "alpha_financials.xlsx", index=False)
    (alpha_dir / "alpha_metadata.json").write_text(
        json.dumps(
            {"company": "AlphaBank", "country": "Uzbekistan", "language": "ru", "year": 2024},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    silk_dir = output_root / "SilkRoadInvest"
    silk_dir.mkdir(parents=True, exist_ok=True)
    _write_pdf(
        silk_dir / "silk_commentary_uz.pdf",
        [
            "SilkRoadInvest 2024 yillik sharhi. Raqamli xizmatlar kengaydi.",
            "Daromad va foyda o'sishi operatsion samaradorlik bilan qo'llab-quvvatlandi.",
        ],
    )
    pd.DataFrame(
        {"Ko'rsatkich": ["Daromad", "Foyda", "Aktivlar"], "2024": [980, 210, 2450]}
    ).to_excel(silk_dir / "silk_financials_uz.xlsx", index=False)
    (silk_dir / "silk_profile.json").write_text(
        json.dumps(
            {"company": "SilkRoadInvest", "country": "Uzbekistan", "language": "uz", "currency": "UZS"},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    mixed_dir = output_root / "MixedHoldings"
    mixed_dir.mkdir(parents=True, exist_ok=True)
    _write_pdf(
        mixed_dir / "mixed_bilingual.pdf",
        [
            "MixedHoldings annual note 2024. Risk management remained conservative.",
            "Выручка укрепилась, daromad esa barqaror oshdi.",
        ],
    )
    pd.DataFrame(
        {"Metric": ["Revenue", "Profit"], "2024": ["1 760", "430"]}
    ).to_excel(mixed_dir / "mixed_financials.xlsx", index=False)
    (mixed_dir / "mixed_metadata.json").write_text(
        json.dumps(
            {"company": "MixedHoldings", "language": "en/ru/uz", "segment": "fintech"},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Example upload files generated at: {output_root}")


if __name__ == "__main__":
    run()
