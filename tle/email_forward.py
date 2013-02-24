import logging
import imaplib
import functools

from contextlib import contextmanager
from email import parser as email_parser

log = logging.getLogger(__name__)

def imap4_cmd(fn):
    functools.wraps(fn)
    def wrapper(*args, **kwargs):
        (code, res) = fn(*args, **kwargs)
        if code != 'OK':
            msg = '{name} failed: {code}, {err}'.format(
                name=fn.__name__,
                code=code,
                err=res,
            )
            raise ValueError(msg)
        # TODO parse res
        return res
    return wrapper

class IMAP4_SSL(imaplib.IMAP4_SSL):
    # TODO add more commands, hopefully not all one by one
    def __init__(self, *args, **kwargs):
        imaplib.IMAP4_SSL.__init__(self, *args, **kwargs)
        self.email_parser = email_parser.Parser()

    @imap4_cmd
    def select(self, *args, **kwargs):
        return imaplib.IMAP4_SSL.select(self, *args, **kwargs)

    @imap4_cmd
    def search(self, *args, **kwargs):
        (code, data) = imaplib.IMAP4_SSL.search(self, *args, **kwargs)
        assert len(data) == 1
        data = data[0].split()
        return (code, data)

    @imap4_cmd
    def fetch(self, *args, **kwargs):
        (code, data) = imaplib.IMAP4_SSL.fetch(self, *args, **kwargs)
        assert len(data) == 2
        assert len(data[0]) == 2
        data = self.email_parser.parsestr(data[0][1])
        return (code, data)

@contextmanager
def mailbox(
        username,
        password,
        server,
        name='INBOX',
        readonly=False,
):
    mail = IMAP4_SSL(server)
    try:
        mail.login(username, password)
        res = mail.select(name, readonly)
        msg = 'Connected to mailbox {name}: {res}'.format(
            name=name,
            res=res,
        )
        log.debug(msg)
        yield mail
    finally:
        try:
            mail.close()
        except IMAP4_SSL.error:
            # TODO can we check if it's open instead?
            pass
        try:
            mail.logout()
        except IMAP4_SSL.error:
            # TODO can we check if we're logged in instead?
            pass

def _forwarded_text(msg):
    data = msg.get_payload()
    if msg.is_multipart():
        data = data[0].get_payload()
    data = data.split('\r\n')
    text = None
    for (i,line) in enumerate(data):
        if '---------- Forwarded message ----------' == line:
            text = data[i+1:i+5]
            break
    return text

def _forwarded_headers(box, text):
    text = '\r\n'.join(text)
    headers = box.email_parser.parsestr(text, headersonly=True)
    return headers

def _forwarded_from(headers):
    # TODO extract user email (maybe first and last name)
    from_user = headers.get('From')
    from_user = dict([
        ('email', from_user),
        ('first_name', 'Friendly'),
        ('last_name', 'Purchaser'),
    ])
    return from_user

def _unprocessed_emails(box):
    # TODO get _unprocessed_emails
    msg = box.fetch('5', '(RFC822)')
    return [msg]

def _forwarding_user(
        box,
        msg,
        to_addr,
        fwd_addr,
        subject=None,
):
    msg_to = msg.get('Delivered-To')
    if msg_to is None:
        err = 'Did not find a Delivered-To address'
        log.error(err)
        return
    if msg_to.lower() != fwd_addr.lower():
        err = 'Found unexpected Delivered-To address: {msg_to}'.format(
            msg_to=repr(msg_to),
        )
        log.error(err)
        return
    if subject is not None:
        msg_subject = msg.get('Subject')
        if msg_subject != 'Fwd: ' + subject:
            err = 'Found unexpected forwarded Subject: {msg_subject}'.format(
                msg_subject=repr(msg_subject),
            )
            log.error(err)
            return
    text = _forwarded_text(msg)
    if text is None:
        err = 'Did not find forwarding info in message'
        log.error(err)
        return
    headers = _forwarded_headers(box, text)
    headers_to = headers.get('To')
    if headers_to.lower() != to_addr.lower():
        err = (
            'Found unexpected To address in forwarding info: '
            '{headers_to}'.format(
                headers_to=repr(headers_to),
            )
        )
        log.error(err)
        return
    if subject is not None:
        headers_subject = headers.get('Subject')
        if headers_subject != subject:
            err = (
                'Found unexpected Subject in forwarding info: '
                '{headers_subject}'.format(
                    headers_subject=repr(headers_subject),
                )
            )
            log.error(err)
            return
    return _forwarded_from(headers)

def create_kajabi_user(
        session,
        kajabi_key,
        kajabi_url,
        kajabi_funnel,
        kajabi_offer,
        email,
        first_name,
        last_name,
):
    # id can be omitted
    params = dict([
        ('api_key', kajabi_key),
        ('kjbf', kajabi_funnel),
        ('kjbo', kajabi_offer),
        ('email', email),
        ('first_name', first_name),
        ('last_name', last_name),
    ])
    log.debug(
        'Creating Kajabi account for email {email}'.format(
            email=email,
        )
    )
    res = session.post(kajabi_url, params=params)
    if res.text != '1' or res.status_code != 200:
        # res.text can contain a lot more than just a number
        msg = (
            'Kajabi account creation for email {email} failed with '
            'status code {code}'.format(
                email=email,
                code=res.status_code,
                )
            )
        log.error(msg)
        # TODO retry
        return False
    log.debug(
        'Received an OK response from Kajabi while creating an '
        'account for email {email}'.format(
            email=email,
        )
    )

def new_users(
        username,
        password,
        server,
        to_addr,
        fwd_addr,
        subject,
):
    with mailbox(username, password, server) as box:
        msgs = _unprocessed_emails(box)
        for msg in msgs:
            user = _forwarding_user(
                box,
                msg,
                to_addr,
                fwd_addr,
                subject,
            )
            if user:
                yield user
