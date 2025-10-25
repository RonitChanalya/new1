# Recovery Runbook (quick)

1. Detect suspicious behavior -> alert.
2. Run `python admin_tools.py` functions or use UI:
   - `set_mode('shadow')`
   - `rotate_api_key()` and `rotate_feature_hmac()`
3. Snapshot current models:
   - `snapshot_model()`
4. Pause ingestion (or stop detector service).
5. Collect buffer / logs: `data/ml_buffer.jsonl`, `data/shadow.log`.
6. Rebuild model safely:
   - `python simulate_attack.py` (to generate adversarial examples for training)
   - `python robust_retrain.py`
7. Validate offline (run detection on test sets).
8. Put model into `shadow` mode for 24–72h and analyze `shadow.log`.
9. Canary enable then full `live` mode.
