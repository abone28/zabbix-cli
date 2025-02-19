#!/usr/bin/env python
#
# Authors:
# rafael@e-mc2.net / https://e-mc2.net/
#
# Copyright (c) 2014-2017 USIT-University of Oslo
#
# This file is part of Zabbix-cli
# https://github.com/unioslo/zabbix-cli
#
# Zabbix-CLI is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Zabbix-CLI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Zabbix-CLI.  If not, see <http://www.gnu.org/licenses/>.
import sys
import os
import getpass
import argparse
import logging
import textwrap

from zabbix_cli.config import get_config, validate_config
from zabbix_cli.logs import configure_logging, LogContext
from zabbix_cli.cli import zabbixcli


logger = logging.getLogger('zabbix-cli')


def main():
    
    try:

        #
        # Processing command line parameters
        #

        output_format = ''
        zabbix_command = ''
        input_file = ''

        parser = argparse.ArgumentParser(prog=sys.argv[0],
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description=textwrap.dedent('''\
                                         
                                         =======
                                          About
                                         =======

                                         Zabbix-CLI is a command-line interface for the Zabbix monitoring system. 
                                         It is a terminal client for managing some Zabbix administration tasks 
                                         via the zabbix-API.
                                         ''')
                                         ,epilog=textwrap.dedent('''\
                                         
                                         ================
                                          Initialization
                                         ================

                                         '/usr/bin/zabbix-cli-init -z YOUR_ZABBIX_URL' has to be run before you start using zabbix-cli for the first time.

                                         ==========
                                          Examples
                                         ==========

                                         Run Zabbix-CLI in interactive mode:
                                         # zabbix-cli

                                         Get all zabbix-CLI commands in command-line mode:
                                         # zabbix-cli -C "help"
                                         
                                         Get help for the zabbix-CLI command 'update_host_proxy' in command-line mode:
                                         # zabbix-cli -C "help update_host_proxy"

                                         Change the proxy definition for a host in command-line mode:
                                         # zabbix-cli -o json -C "update_host_proxy myhost.domain.net zbx-proxy.domain.net"
                                         
                                         =======
                                          Links
                                         =======

                                         The latest information and versions of Zabbix-CLI can be obtained 
                                         from: https://e-mc2.net/zabbix-cli

                                         The latest Zabbix-CLI documentation is available from:
                                         https://github.com/unioslo/zabbix-cli/blob/master/docs/manual.rst

                                         '''))

        parser.add_argument(
            '-c',
            required=False,
            dest='config_file',
            help="Define an alternative configuration file.")
        parser.add_argument(
            '-C',
            required=False,
            dest='zabbix_command',
            help="Zabbix-CLI command to execute when running in command-line mode.")
        parser.add_argument(
            '-f',
            required=False,
            dest='input_file',
            help="File with Zabbix-CLI commands to be executed in bulk mode.")
        parser.add_argument(
            '-o',
            choices=['csv', 'json', 'table'],
            required=False,
            dest='output_format',
            help="Define the output format when running in command-line mode.")

        args = parser.parse_args()

        if args.output_format:
            output_format = args.output_format

        if args.zabbix_command:
            zabbix_command = args.zabbix_command

        if args.input_file:
            input_file = args.input_file

        conf = get_config(args.config_file)
        validate_config(conf)
        configure_logging(conf)

        #
        # If logging is activated, start logging to the file defined
        # with log_file in the config file.
        #

        logger.debug('**** Zabbix-CLI startet. ****')

        #
        # Non-interactive authentication procedure
        #
        # If the file .zabbix_cli_auth exists at $HOME, use the
        # information in this file to authenticate into Zabbix API
        #
        # Format:
        # <Zabbix username>::<password>
        #
        # Use .zabbix-cli_auth_token if it exists and .zabbix_cli_auth
        # does not exist.
        #
        # Format:
        # <Zabbix username>::<API-token>
        #

        auth_token = ''
        username = ''
        password = ''
        zabbix_auth_file = ''
        zabbix_auth_token_file = ''

        if os.getenv('HOME') is not None:

            zabbix_auth_file = os.getenv('HOME') + '/.zabbix-cli_auth'
            zabbix_auth_token_file = os.getenv('HOME') + '/.zabbix-cli_auth_token'

        else:
            print('\n[ERROR]: The $HOME environment variable is not defined. Zabbix-CLI cannot read ~/.zabbix-cli_auth or ~/.zabbix-cli_auth_token')

            logger.error('The $HOME environment variable is not defined. Zabbix-CLI cannot read ~/.zabbix-cli_auth or ~/.zabbix-cli_auth_token')

            sys.exit(1)

        env_username = os.getenv('ZABBIX_USERNAME')
        env_password = os.getenv('ZABBIX_PASSWORD')

        if env_username is not None and env_password is not None:

            username = env_username
            password = env_password

            logger.info('Environment variables ZABBIX_USERNAME and ZABBIX_PASSWORD exist. Using these variables to get authentication information')

        elif os.path.isfile(zabbix_auth_file):

            try:
                # TODO: This should be done when writing the file.
                #       If permissions are wrong here, we should refuse using
                #       it, ssh style.
                os.chmod(zabbix_auth_file, 0o400)

                with open(zabbix_auth_file, 'r') as f:
                    for line in f:
                        (username, password) = line.split('::')

                password = password.replace('\n', '')
                logger.info('File %s exists. Using this file to get authentication information', zabbix_auth_file)

            except Exception as e:

                print('\n[ERROR]:' + str(e) + '\n')

                logger.error('Problems using file %s - %s', zabbix_auth_file, e)

        elif os.path.isfile(zabbix_auth_token_file):

            try:
                # TODO: This should be done when writing the file.
                #       If permissions are wrong here, we should refuse using
                #       it, ssh style.
                os.chmod(zabbix_auth_token_file, 0o600)

                with open(zabbix_auth_token_file, 'r') as f:
                    for line in f:
                        (username, auth_token) = line.split('::')

                logger.info('File %s exists. Using this file to get authentication token information', zabbix_auth_token_file)

            except Exception as e:
              
                print('\n[ERROR]:' + str(e) + '\n')

                logger.error('Problems using file %s - %s', zabbix_auth_token_file, e)


        #
        # Interactive authentication procedure
        #

        else:

            default_user = getpass.getuser()
            
            print('-------------------------')
            print('Zabbix-CLI authentication')
            print('-------------------------')
        

            try:
                username = input('# Username[' + default_user +']: ')
                password = getpass.getpass('# Password: ')

            except Exception as e:
                print('\n[Aborted]\n')
                sys.exit(0)

            if username == '':
                username = default_user


        #
        # Check that username and password have some values if the
        # API-auth-token is empty ($HOME/.zabbix-cli_auth_token does
        # not exist)
        #

        if auth_token == '':

            if username == '' or password == '':

                print('\n[ERROR]: Username or password is empty\n')
                logger.error('Username or password is empty')

                sys.exit(1)

        with LogContext(logger, user=username):

            #
            # Zabbix-CLI in interactive modus
            #

            if zabbix_command == '' and input_file == '':

                logger.debug('Zabbix-CLI running in interactive modus')

                os.system('clear')

                cli = zabbixcli(conf, username, password, auth_token)

                cli.cmdloop()

            #
            # Zabbix-CLI in bulk execution modus.
            #
            # This mode is activated when we run zabbix-cli with the
            # parameter -f to define a file with zabbix-cli commands.
            #

            elif zabbix_command == '' and input_file != '':

                cli = zabbixcli(conf, username, password, auth_token)

                # Normalized absolutized version of the pathname if
                # files does not include an absolute path

                if os.path.isabs(input_file) is False:
                    input_file = os.path.abspath(input_file)

                if os.path.exists(input_file):

                    logger.info('File [%s] exists. Bulk execution of commands defined in this file.', input_file)

                    print('[OK] File [' + input_file + '] exists. Bulk execution of commands defined in this file started.')

                    #
                    # Register that this is a bulk execution via -f
                    # parameter. This will activate some performance
                    # improvements to boost bulk execution.
                    #

                    cli.bulk_execution = True
     
                    # Register CSV output format

                    if output_format == 'csv':
                        cli.output_format = 'csv'

                    # Register JSON output format

                    elif output_format == 'json':
                        cli.output_format = 'json'

                    # Register Table output format

                    else:
                        cli.output_format = 'table'

                    #
                    # Processing zabbix commands in file.
                    #
                    # Empty lines or comment lines (started with #) will
                    # not be considered.

                    try:
                        with open(input_file, 'r') as f:

                            for input_line in f:

                                if input_line.find('#', 0) == -1 and input_line.strip() != '':

                                    zabbix_cli_command = input_line.strip()
                                    cli.onecmd(zabbix_cli_command)

                                    logger.info('Zabbix-cli command [%s] executed via input file', zabbix_cli_command)

                    except Exception as e:

                        logger.error('Problems using input file [%s] - %s', input_file, e)

                        print('[ERROR] Problems using input file [' + input_file + '] - ' + str(e))
                        sys.exit(1)

                else:

                    logger.info('Input file [%s] does not exist. Bulk execution of commands aborted.', input_file)

                    print('[ERROR] Input file [' + input_file + '] does not exist. Bulk execution of commands aborted')


            #
            # Zabbix-CLI in non-interactive modus(command line)
            #

            elif zabbix_command != '':

                logger.debug('Zabbix-CLI running in non-interactive modus')

                # CSV format output

                if output_format == 'csv':

                    cli = zabbixcli(conf, username, password, auth_token)
                    cli.output_format = 'csv'
                    cli.non_interactive = True

                    cli.onecmd(zabbix_command)

                # JSON format output

                elif output_format == 'json':

                    cli = zabbixcli(conf, username, password, auth_token)
                    cli.output_format = 'json'
                    cli.non_interactive = True

                    cli.onecmd(zabbix_command)

                # Table format output

                else:
                    cli = zabbixcli(conf, username, password, auth_token)
                    cli.output_format = 'table'
                    cli.non_interactive = True

                    cli.onecmd(zabbix_command)

            else:
                raise NotImplementedError

            logger.debug('**** Zabbix-CLI stopped. ****')

        sys.exit(0)

    except KeyboardInterrupt:
        print()
        print("\nDone, thank you for using Zabbix-CLI")

        logger.debug('**** Zabbix-CLI stopped. ****')

        sys.exit(0)

    except Exception as e:
        print('\n[ERROR]:' + str(e) + '\n')

if __name__ == '__main__':
    main()
