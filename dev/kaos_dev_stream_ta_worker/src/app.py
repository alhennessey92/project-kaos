import time
import sys
import traceback
import logging

from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.oauth2 import service_account


project_id = "project-kaos"
publish_topic_id = "kaos_dev_ig_zeus_input_eurusd"
credentials = service_account.Credentials.from_service_account_file('project-kaos-3c01956c9113.json')

def zeusInput(sanitised_data):
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    topic_path = publisher.topic_path(project_id, publish_topic_id)

    futures = dict()

    def get_callback(f, data):
        def callback(f):
            try:
                print(str(f.result(), 'utf-8'))
                # print(f.result())
                futures.pop(data)
            except:  # noqa
                print("Please handle {} for {}.".format(f.exception(), data))

        return callback

    
    futures.update({sanitised_data: None})
    # When you publish a message, the client returns a future.
    future = publisher.publish(topic_path, sanitised_data.encode("utf-8"))
    futures[sanitised_data] = future
    # Publish failures shall be handled in the callback function.
    future.add_done_callback(get_callback(future, sanitised_data))
    




if __name__ == "__main__":
    # TODO(developer)
    
    subscription_id = "kaos_dev_ig_input_eurusd-sub"
    # Number of seconds the subscriber should listen for messages
    timeout = 50.0
    

    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    # The `subscription_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/subscriptions/{subscription_id}`
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    def callback(message):
        print(f"Received {message}.")
        message.ack()
        sanitised_data = str(message)
        zeusInput(sanitised_data)

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

