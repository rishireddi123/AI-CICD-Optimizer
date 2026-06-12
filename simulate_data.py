# simulate_data.py

import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("pipeline.db")

runs = [
    ('fake-run-1', 'failure', 'FAILED test_divide: AssertionError assert 12 == 15'),
    ('fake-run-2', 'success', 'All tests passed successfully'),
    ('fake-run-3', 'failure', 'FAILED test_divide: AssertionError assert 12 == 15'),
    ('fake-run-4', 'success', 'All tests passed successfully'),
    ('fake-run-5', 'failure', 'FAILED test_divide: AssertionError assert 12 == 15'),
    ('fake-run-6', 'success', 'All tests passed successfully'),
    ('fake-run-7', 'failure', 'FAILED test_divide: AssertionError assert 12 == 15'),
    ('fake-run-8', 'success', 'All tests passed successfully'),
    ('fake-run-9', 'failure', 'FAILED test_divide: AssertionError assert 12 == 15'),
    ('fake-run-10', 'success', 'All tests passed successfully'),
]

for i, (run_id, status, log) in enumerate(runs):
    ts = datetime.now() - timedelta(hours=i*3)
    conn.execute(
        'INSERT INTO runs (run_id, repo, status, log_text, root_cause, fix_suggestion, severity, timestamp) VALUES (?,?,?,?,?,?,?,?)',
        (run_id, 'rishireddi123/AI-CICD-Optimizer', status, log, 'Test assertion error', 'Fix the test', 'low', ts)
    )

conn.commit()
conn.close()
print('Inserted 10 simulated runs successfully.')