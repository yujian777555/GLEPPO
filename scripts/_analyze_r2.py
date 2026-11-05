import json
with open("research/G3_DIAG_R2_RAW.json") as f:
    d = json.load(f)

for tid in ["B2-002"]:
    info = d["baseline"][tid]
    print(f"=== {tid} ===")
    print(f"  tool_path_passed: {info['tool_path_passed']}")
    for tr in info["traces"]:
        tp = tr["tool_path_details"]
        print(f"  success: {tr['success']}, answer: {tr['answer'][:150]}")
        print(f"  contract: {tp.get('contract', [])}")
        print(f"  successful_sequence: {tp.get('successful_sequence', [])}")
        print(f"  missing_or_wrong: {tp.get('missing_or_wrong', [])}")
        print(f"  all_tool_events: {tp.get('all_tool_events', [])}")
        for e in tr["trace"]:
            print(f"    {e}")
