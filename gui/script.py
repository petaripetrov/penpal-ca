import sys

print("Python script started")
sys.stdout.flush()  # Ensure Java gets output immediately

while True:
    user_input = input()
    if user_input.lower() == "exit":
        print("Python script exiting...")
        sys.stdout.flush()
        break
    print(f"Python received: {user_input}")
    sys.stdout.flush()
