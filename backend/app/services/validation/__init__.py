"""Phase 7 validation harness: held-out evaluation, honest metrics, evidence.

Evaluates the frozen MVP analytics against held-out synthetic scenarios and
persists reproducible ``validation_runs`` / ``ground_truth_labels`` /
``metric_results`` rows. Nothing here tunes engines — it only measures them.
"""
