# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import requests
import datetime

from flask import Blueprint, request, jsonify

from rasa_core.channels.channel import UserMessage, OutputChannel
from rasa_core.channels.rest import HttpInputComponent

logger = logging.getLogger(__name__)

MICROSOFT_OAUTH2_URL = 'https://login.microsoftonline.com'
MICROSOFT_OAUTH2_PATH = 'botframework.com/oauth2/v2.0/token'


class BotFramework(OutputChannel):
    """A Microsoft Bot Framework communication channel."""

    token_expiration_date = datetime.datetime.now()
    headers = None

    def __init__(self, bf_id, bf_secret, conversation, bot_id,
                 service_url):
        # type: (Text, Text, Dict[Text], Text, Text) -> None

        self.bf_id = bf_id
        self.bf_secret = bf_secret
        self.conversation = conversation
        self.global_uri = "{}v3/".format(service_url)
        self.bot_id = bot_id

    def get_headers(self):
        if BotFramework.token_expiration_date < datetime.datetime.now():
            uri = "{}/{}".format(MICROSOFT_OAUTH2_URL, MICROSOFT_OAUTH2_PATH)
            grant_type = 'client_credentials'
            scope = 'https://api.botframework.com/.default'
            payload = {'client_id': self.bf_id,
                       'client_secret': self.bf_secret,
                       'grant_type': grant_type,
                       'scope': scope}

            token_response = requests.post(uri, data=payload)
            if token_response.ok:
                token_data = token_response.json()
                access_token = token_data['access_token']
                token_expiration = token_data['expires_in']
                BotFramework.token_expiration_date = \
                    datetime.datetime.now() + \
                    datetime.timedelta(seconds=int(token_expiration))
                BotFramework.headers = {"content-type": "application/json",
                                 "Authorization": "Bearer %s" % access_token}
                return BotFramework.headers
            else:
                logger.error('Could not get BotFramework token')
        else:
            return BotFramework.headers

    def send(self, recipient_id, message_data):
        # type: (Text, Dict[Text, Any]) -> None

        post_message_uri = self.global_uri + \
            'conversations/{}/activities'.format(self.conversation['id'])
        data = {"type": "message",
                "recipient": {
                    "id": recipient_id
                },
                "from": self.bot_id,
                "channelData": {
                    "notification": {
                        "alert": "true"
                    }
                },
                "text": ""}

        data.update(message_data)
        headers = self.get_headers()
        send_response = requests.post(post_message_uri,
                             headers=headers,
                             data=json.dumps(data))

        if not send_response.ok:
            logger.error('Error in send: %s', send_response.text)

    def send_text_message(self, recipient_id, message):
        logger.info("Sending message: " + message)

        text_message = {"text": message}
        self.send(recipient_id, text_message)

    def send_image_url(self, recipient_id, image_url):
        hero_content = {
            'contentType': 'application/vnd.microsoft.card.hero',
            'content': {
                'images': [{'url': image_url}]
                }
            }

        image_message = {"attachments": [hero_content]}
        self.send(recipient_id, image_message)

    def send_text_with_buttons(self, recipient_id, message, buttons, **kwargs):
        hero_content = {
            'contentType': 'application/vnd.microsoft.card.hero',
            'content': {
                'subtitle': message,
                'buttons': buttons
                }
            }

        buttons_message = {"attachments": [hero_content]}
        self.send(recipient_id, buttons_message)

    def send_custom_message(self, recipient_id, elements):
        self.send(recipient_id, elements[0])


class BotFrameworkInput(HttpInputComponent):
    """Bot Framework input channel implementation."""

    def __init__(self, bf_id, bf_secret):
        # type: (Text, Text) -> None
        """Create a Bot Framework input channel.

        :param bf_id: Bot Framework's API id
        :param bf_secret: Bot Framework application secret
        """

        self.bf_id = bf_id
        self.bf_secret = bf_secret

    def blueprint(self, on_new_message):

        bf_webhook = Blueprint('bf_webhook', __name__)

        @bf_webhook.route("/", methods=['GET'])
        def health():
            return jsonify({"status": "ok"})

        @bf_webhook.route("/api/messages", methods=['POST'])
        def webhook():
            postdata = request.get_json(force=True)
            logger.info(json.dumps(postdata, indent=4))
            try:
                if postdata["type"] == "message":
                    out_channel = BotFramework(self.bf_id, self.bf_secret,
                                               postdata["conversation"],
                                               postdata["recipient"],
                                               postdata["serviceUrl"])
                    text = ""
                    value = ""
                    if postdata.get("value"):
                        raw_value = postdata.get("value")
                        # value = raw_value.get("value")
                        value = raw_value
                    else:
                        if postdata.get("text"):
                            text = postdata.get("text")
                    
                    user_msg = UserMessage("{}{}".format(text, json.dumps(value)), 
                                           out_channel,
                                           postdata["from"]["id"])
                    on_new_message(user_msg)
                else:
                    logger.info("Not received message type")
            except Exception as e:
                logger.error("Exception when trying to handle "
                             "message.{0}".format(e))
                logger.error(e, exc_info=True)
                pass

            return "success"

        return bf_webhook
