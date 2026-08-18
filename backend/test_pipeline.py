import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from backend.validator import validator
from backend.feature_store import feature_extractor
from backend.model_engine import risk_engine
from backend.listener import simulator

def test_full_pipeline():
    print("=" * 70)
    print("RUNNING E2E PIPELINE & TREESHAP LATENCY VERIFICATION")
    print("=" * 70)

    # 0. Warmup TreeSHAP matrix
    _ = risk_engine.evaluate(feature_extractor.extract_features(validator.validate_and_parse(simulator.generate_transaction())))

    # 1. Generate normal EVM transaction
    normal_payload = simulator.generate_transaction()
    start_time = time.time()

    val_tx = validator.validate_and_parse(normal_payload)
    assert val_tx is not None, "Validation failed for normal payload"

    features = feature_extractor.extract_features(val_tx)
    assert "gas_spike_ratio" in features, "Feature extraction failed"

    eval_result = risk_engine.evaluate(features)
    elapsed_ms = (time.time() - start_time) * 1000.0

    print(f"[Baseline Tx Test] Composite Risk Score: {eval_result['composite_risk_score']} ({eval_result['alert_level']})")
    print(f"[Baseline Tx Test] TreeSHAP Execution Latency: {eval_result['execution_time_ms']} ms")
    print(f"[Baseline Tx Test] Total Pipeline Execution Time: {elapsed_ms:.2f} ms")
    assert eval_result['execution_time_ms'] < 30.0, "TreeSHAP SLA exceeded 30ms limit!"

    # 2. Generate malicious attack payload (Tornado Cash Interaction)
    print("-" * 70)
    attack_payload = simulator.generate_transaction(attack_mode="TORNADO_SANCTION")
    
    val_attack = validator.validate_and_parse(attack_payload)
    features_attack = feature_extractor.extract_features(val_attack)
    eval_attack = risk_engine.evaluate(features_attack)

    print(f"[Attack Tx Test] Composite Risk Score: {eval_attack['composite_risk_score']} ({eval_attack['alert_level']})")
    print(f"[Attack Tx Test] Top SHAP Drivers / Reasons:")
    for reason in eval_attack['reasons']:
        print(f"   -> {reason}")

    assert eval_attack['composite_risk_score'] >= 90.0, "Tornado Cash interaction did not trigger CRITICAL alert!"
    assert eval_attack['alert_level'] == "CRITICAL", "Alert level must be CRITICAL"

    print("=" * 70)
    print("ALL PIPELINE TESTS & LATENCY SLAs VERIFIED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_pipeline()
