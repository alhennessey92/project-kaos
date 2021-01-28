import time
import sys
import traceback
import logging

from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.oauth2 import service_account

# TODO(developer)
project_id = "project-kaos"
subscription_id = "kaos_dev_ig_input_eurusd-sub"
# Number of seconds the subscriber should listen for messages
timeout = 50.0
credentials = service_account.Credentials.from_service_account_file('project-kaos-ca46ef0355fc.json')

subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
# The `subscription_path` method creates a fully qualified identifier
# in the form `projects/{project_id}/subscriptions/{subscription_id}`
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message):
    print(f"Received {message}.")
    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")

# Wrap subscriber in a 'with' block to automatically call close() when done.
with subscriber:
    try:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        streaming_pull_future.result(timeout=timeout)
    except TimeoutError:
        streaming_pull_future.cancel()

