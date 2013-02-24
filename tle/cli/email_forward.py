import argparse
import requests
import logging

from tle.email_forward import (
    new_users,
    create_kajabi_user,
)
from tle.util.config import (
    config_parser,
    config_list,
    )

log = logging.getLogger(__name__)

# Disable annoying "HTTP connection" log lines from the requests module
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

def main():
    parser = argparse.ArgumentParser(
        description='Create Kajabi user from forwarded emails',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False,
        help='output DEBUG logging statements (default: %(default)s)',
        )
    parser.add_argument(
        '--config',
        help=('path to the file with information on how to '
              'configure the service'
              ),
        required=True,
        metavar='PATH',
        type=str,
        )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s.%(msecs)03d %(name)s: %(levelname)s: %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
        )
    config = config_parser(args.config)
    session = requests.Session()
    to_addrs = config_list(config, 'email', 'to_addrs')

    log.info('Starting')
    for user in new_users(
            username=config.get('email', 'username'),
            password=config.get('email', 'password'),
            server=config.get('email', 'server'),
            to_addrs=to_addrs,
            fwd_addr=config.get('email', 'fwd_addr'),
            subject=None,
    ):
        create_kajabi_user(
            session=session,
            kajabi_key=config.get('kajabi', 'key'),
            kajabi_url=config.get('kajabi', 'url'),
            kajabi_funnel=config.get('kajabi', 'funnel'),
            kajabi_offer=config.get('kajabi', 'offer'),
            email=user['email'],
            first_name=user['first_name'],
            last_name=user['last_name'],
        )
    log.info('Finished')