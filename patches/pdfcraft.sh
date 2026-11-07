#!/usr/bin/env bash
# PdfKoja: ocrs-models' S3 bucket answers 403 since November 2026. Fetch the same two OCR models
# (same SHA-256, checked by `cargo xtask models`) from Kojalytics' mirror instead.
set -euo pipefail
perl -pi -e 's{https://ocrs-models\.s3-accelerate\.amazonaws\.com/(text-(?:detection|recognition)\.rten)}{https://github.com/Kojalytics/koja-brand/releases/download/ocr-models-1/$1}g' ATTRIBUTION.toml
