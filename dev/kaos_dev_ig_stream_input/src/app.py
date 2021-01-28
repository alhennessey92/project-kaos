import time
import sys
import traceback
import logging

from trading_ig import IGService, IGStreamService
from trading_ig.config import config
from trading_ig.lightstreamer import Subscription

from google.cloud import pubsub_v1
from google.oauth2 import service_account


# A simple function acting as a Subscription listener
def on_prices_update(item_update):
    print("price: %s " % item_update, flush=True)
    # print(
    #     "{stock_name:<19}: Time {UPDATE_TIME:<8} - "
    #     "Bid {BID:>5} - Ask {OFFER:>5}".format(
    #         stock_name=item_update["name"], **item_update["values"]
    #     ), flush=True
    # )

def on_heartbeat_update(item_update):
    print(item_update["values"])

def on_account_update(balance_update):
    print("balance: %s " % balance_update, flush=True)


def main():
    logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)

    ig_service = IGService(
        config.username, config.password, config.api_key, config.acc_type
    )

    ig_stream_service = IGStreamService(ig_service)
    ig_session = ig_stream_service.create_session()
    # Ensure configured account is selected
    accounts = ig_session[u"accounts"]
    for account in accounts:
        if account[u"accountId"] == config.acc_number:
            accountId = account[u"accountId"]
            break
        else:
            print("Account not found: {0}".format(config.acc_number))
            accountId = None
    ig_stream_service.connect(accountId)

    # Making a new Subscription in MERGE mode
    # subscription_prices = Subscription(
    #     mode="MERGE",
    #     items=["MARKET:CS.D.EURUSD.TODAY.IP"],
    #     fields=["UPDATE_TIME", "BID", "OFFER", "CHANGE", "MARKET_STATE"]
    #     # adapter="QUOTE_ADAPTER"
    # )
    subscription_prices = Subscription(
        mode="MERGE",
        items=["CHART:CS.D.EURUSD.TODAY.IP:15MINUTE"],
        fields=["BID_OPEN"]
    )
    # adapter="QUOTE_ADAPTER")

    # Adding the "on_price_update" function to Subscription
    subscription_prices.addlistener(on_prices_update)

    # Registering the Subscription
    sub_key_prices = ig_stream_service.ls_client.subscribe(subscription_prices)

    # Making an other Subscription in MERGE mode
    subscription_account = Subscription(
        mode="MERGE", items=["ACCOUNT:" + accountId], fields=["AVAILABLE_CASH"],
    )
    #    #adapter="QUOTE_ADAPTER")

    # Adding the "on_balance_update" function to Subscription
    subscription_account.addlistener(on_account_update)

    # Registering the Subscription
    sub_key_account = ig_stream_service.ls_client.subscribe(subscription_account)

    heartbeat_items = ["TRADE:HB.U.HEARTBEAT.IP"]
    heartbeat = Subscription(
        mode='MERGE',
        items=heartbeat_items,
        fields=["HEARTBEAT"],
    )

    heartbeat.addlistener(on_heartbeat_update)
    sub_heartbeat = ig_stream_service.ls_client.subscribe(heartbeat)

    input(
        "{0:-^80}\n".format(
            "HIT CR TO UNSUBSCRIBE AND DISCONNECT FROM \
    LIGHTSTREAMER"
        )
    )

    # Disconnecting
    ig_stream_service.disconnect()

    


if __name__ == "__main__":
    # main()
    credentials = service_account.Credentials.from_service_account_file('project-kaos-ca46ef0355fc.json')
    project_id = "project-kaos"
    topic_id = "kaos_dev_ig_input_eurusd"

    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    topic_path = publisher.topic_path(project_id, topic_id)

    futures = dict()

    def get_callback(f, data):
        def callback(f):
            try:
                print(f.result())
                futures.pop(data)
            except:  # noqa
                print("Please handle {} for {}.".format(f.exception(), data))

        return callback

    for i in range(10):
        data = str(i)
        futures.update({data: None})
        # When you publish a message, the client returns a future.
        future = publisher.publish(topic_path, data.encode("utf-8"))
        futures[data] = future
        # Publish failures shall be handled in the callback function.
        future.add_done_callback(get_callback(future, data))

    # Wait for all the publish futures to resolve before exiting.
    while futures:
        time.sleep(5)

    print(f"Published messages with error handler to {topic_path}.")






# if __name__ == '__main__':
#     a = 0
#     while a < 1:
#         print("Hello Al")
