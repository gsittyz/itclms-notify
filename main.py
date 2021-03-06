from flask import Flask, request, abort
import os

from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)
import itclms_scraper
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)

# 環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["LINE_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["LINE_SECRET"]
YOUR_LINE_ID = os.environ["LINE_ID"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


@app.route("/")
def hello_world():
    return "hello world!"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.reply_token == "00000000000000000000000000000000":
        return
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="待ってね"))
    lecture_infos = itclms_scraper.scrape()
    assignments = itclms_scraper.submit_check(lecture_infos)
    text = itclms_scraper.to_text(assignments)
    line_bot_api.push_message(YOUR_LINE_ID,
                              messages=TextSendMessage(text=text))


if __name__ == "__main__":
    #    app.run()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
