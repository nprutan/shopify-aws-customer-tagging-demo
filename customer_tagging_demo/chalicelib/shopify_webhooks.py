import os

CHALICE_URL = os.environ.get('CHALICE_URL', "https://example.amazonaws.com/api/orders")

orders_create = {
  "webhook": {
    "topic": "orders/create",
    "address": CHALICE_URL,
    "format": "json"
  }
}

orders_cancelled = {
  "webhook": {
    "topic": "orders/cancelled",
    "address": CHALICE_URL,
    "format": "json"
  }
}

orders_fulfilled = {
  "webhook": {
    "topic": "orders/fulfilled",
    "address": CHALICE_URL,
    "format": "json"
  }
}

orders_paid = {
  "webhook": {
    "topic": "orders/paid",
    "address": CHALICE_URL,
    "format": "json"
  }
}

orders_updated = {
  "webhook": {
    "topic": "orders/updated",
    "address": CHALICE_URL,
    "format": "json"
  }
}