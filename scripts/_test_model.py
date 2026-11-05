"""Quick test of ProductionLLM."""
import sys
sys.path.insert(0, '.')

from gleppo.llm import ProductionLLM

llm = ProductionLLM(device='cuda:0', max_new_tokens=32, temperature=0.7)
print('Model loaded:', llm.version)

reply = llm.reply('You are a calculator.', 'What is 2+2?', [], ('test', 0, 0))
print('Reply:', reply.text[:100])
print('Stats:', llm.get_stats())
