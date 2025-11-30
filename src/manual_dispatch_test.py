from trading_ai.services.discord.router import dispatch

print("Sending test message...")

dispatch("system_logs", "TEST DISPATCH", "Message from manual_dispatch_test")

print("Done.")
