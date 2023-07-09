import paypalrestsdk

# Replace these with your own client id and secret
paypalrestsdk.configure({
    "mode": "sandbox",  # sandbox or live
    "client_id": "AdKZi8a1LhaQqnmhybR4vj4Rej3wmG-xPzJwM3aYlbF6qBclVwERP0JAXnA1bzWpN2P6jfcDDVpdaaW0",
    "client_secret": "EGn__MUgWdFA1oM6ZLrg8pPzN8XSyWRJZE40z1-I1BwPWETiNJUDqcX4gJgfmZMXU1w5DjQo-dXU40te"})

payment = paypalrestsdk.Payment.find("67B70055MU1231720")

print(payment)
