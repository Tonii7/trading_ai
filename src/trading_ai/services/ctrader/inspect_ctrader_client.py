from ctrader_open_api import Client, TcpProtocol

HOST = "demo.ctraderapi.com"
PORT = 5035

print("📌 Creating TcpProtocol()...")
protocol = TcpProtocol()

print("📌 Creating Client(HOST, PORT, protocol)...")
client = Client(HOST, PORT, protocol)

print("\n✅ Client object created:", client)
print("\n🔍 Доступные методы/атрибуты Client:")

public_attrs = [name for name in dir(client) if not name.startswith("_")]
for name in public_attrs:
    attr = getattr(client, name)
    print(f" - {name} ({type(attr)})")
