#!/usr/bin/env python

from __future__ import absolute_import

import click

from brewtils.plugin import RemotePlugin
from ._version import __version__
from .client import EchoClient


@click.command()
@click.option('--bg-host', help='The beer-garden server FQDN')
@click.option('--bg-port', default=2337, help='The beer-garden server port')
@click.option('--bg-url-prefix', default=None, help='The beer-garden server path')
@click.option('--ssl-enabled/--ssl-disabled', default=False, help='Use SSL when communicating with beer-garden')
@click.option('--ca-verify/--no-ca-verify', default=True, help='Verify server certificate when using SSL')
@click.option('--ca-cert', default=None, help='CA certificate to use when verifying')
def main(bg_host, bg_port, bg_url_prefix, ssl_enabled, ca_verify, ca_cert):

    plugin = RemotePlugin(EchoClient(), name='remote-echo', version=__version__, description='This is a remote plugin.',
                          bg_host=bg_host, bg_port=bg_port, bg_url_prefix=bg_url_prefix, ssl_enabled=ssl_enabled,
                          ca_verify=ca_verify, ca_cert=ca_cert)
    plugin.run()


if __name__ == '__main__':
    main()
