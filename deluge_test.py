# -*- coding: utf-8 -*-
import time
import socket
import vk_api
from deluge_client import DelugeRPCClient as deluge

client = deluge(
    '127.0.0.1',
    58846,
    'pi',
    'raspberry'
)

client.connect()