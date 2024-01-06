# This file is a part of TG-FileStreamBot
# Coding : Jyothis Jayanth [@EverythingSuckz]
import re
from urllib.parse import quote_plus

import urllib.parse
import aria2p
import requests
from pyrogram import filters, errors
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from WebStreamer.bot import StreamBot, logger
from WebStreamer.utils import get_hash, get_name
from WebStreamer.vars import Var


@StreamBot.on_message(
    filters.private
    & (
            filters.document
            | filters.video
            | filters.audio
            | filters.animation
            | filters.voice
            | filters.video_note
            | filters.photo
            | filters.sticker
    ),
    group=4,
)
async def media_receive_handler(_, m: Message):
    if Var.ALLOWED_USERS and not (
            (str(m.from_user.id) in Var.ALLOWED_USERS) or (m.from_user.username in Var.ALLOWED_USERS)):
        return await m.reply("您无权使用该机器人！", quote=True)
    log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)
    file_hash = get_hash(log_msg, Var.HASH_LENGTH)
    stream_link = f"{Var.URL}{log_msg.id}/{quote_plus(get_name(m))}?hash={file_hash}"
    short_link = f"{Var.URL}{file_hash}{log_msg.id}"
    logger.info(f"Generated link: {stream_link} for {m.from_user.first_name}")
    if Var.ARIA2:
        try:
            aria2 = aria2p.API(
                aria2p.Client(
                    host=Var.RPC_URLS,
                    port=Var.RPC_PORTS,
                    secret=Var.RPC_TOKENS
                )
            )
        except aria2p.client.ClientException as e:
            print(f"Aria2密钥错误！error：{e}")
            await m.reply_text(
                text="Aria2密钥错误！任务未自动添加到Aria2！\n<a href='{}'>长链接</a>\t<a href='{}'>短链接</a>\t".format(
                    stream_link, short_link
                ),
                quote=True,
                parse_mode=ParseMode.HTML,
            )
        except requests.exceptions.ConnectionError as e:
            print(f"Aria2 host或者port有误！{e}")
            await m.reply_text(
                text="Aria2 host或者port有误！\n<a href='{}'>长链接</a>\t<a href='{}'>短链接</a>\t".format(
                    stream_link, short_link
                ),
                quote=True,
                parse_mode=ParseMode.HTML,
            )
        else:
            download = aria2.add(stream_link)
            statue = str(download)
            statue = re.sub(r"\[|<|>]", "", statue)
            try:
                await m.reply_text(
                    text="Aria2：{}\n\n文件名：{}\n\nAria2添加成功！\n".format(
                        statue, urllib.parse.unquote(str(download[0]))
                    ),
                    quote=True,
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("打开长连接", url=stream_link)],
                         [InlineKeyboardButton("打开短链接", url=short_link)]]
                    ),
                )
            except errors.ButtonUrlInvalid:
                await m.reply_text(
                    text="Aria2：{}\n\n文件名：{}\n\nAria2添加成功！\n\n<a href='{}'>长链接</a>\t<a href='{}'>短链接</a>\t".format(
                        statue, urllib.parse.unquote(str(download[0])), stream_link, short_link
                    ),
                    quote=True,
                    parse_mode=ParseMode.HTML,
                )

            logger.info(f"已将 {short_link} 发送至aria2！aria2返回消息为 {download} \n")
    else:
        logger.info(f"未启用Aria2！跳过将 {short_link} 发送至aria2！\n")
        try:
            await m.reply_text(
                text="<a href='{}'>长链接</a>\t<a href='{}'>短链接</a>\t".format(
                    stream_link, short_link
                ),
                quote=True,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("打开长连接", url=stream_link)],
                     [InlineKeyboardButton("打开短链接", url=short_link)]]
                ),
            )
        except errors.ButtonUrlInvalid:
            await m.reply_text(
                text="<a href='{}'>长链接</a>\t<a href='{}'>短链接</a>\t".format(
                    stream_link, short_link
                ),
                quote=True,
                parse_mode=ParseMode.HTML,
            )
