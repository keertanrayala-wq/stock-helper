import sys
from datetime import date

from src.move import get_move_evidence

ticker = sys.argv[1]
day = date.fromisoformat(sys.argv[2])
evidence = get_move_evidence(ticker, day)

for key, value in evidence.items():
    if key != "headlines":
        print(f"{key}: {value}")
print("headlines:")
for h in evidence["headlines"]:
    print(" -", h["title"])