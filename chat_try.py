from src.assistant import chat, get_client

client = get_client()
history = []
print("Ask about a stock. Type 'quit' to exit.")
while True:
    q = input("\nYou: ").strip()
    if q.lower() in ("quit", "exit"):
        break
    text, history, calls = chat(client, history, q)
    for name, args in calls:
        print(f"  [used {name} {args}]")
    print(f"\nAssistant: {text}")