# Copyright (C) 2013 Johnny Vestergaard <jkv@unixcluster.dk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import uuid
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


class Session(object):
    authenticator = None
    default_timeout = 25
    hive_id = None

    def __init__(self, attacker_ip, attacker_s_port, protocol, socket, honeypot_port=None, honeypot_ip=None):

        assert Session.authenticator is not None

        self.attacker_ip = attacker_ip
        self.attacker_source_port = attacker_s_port
        self.protocol = protocol
        self.honey_ip = honeypot_ip
        self.honey_port = honeypot_port

        self.id = uuid.uuid4()
        self.timestamp = datetime.utcnow()
        self.connected = True

        self.authenticated = False
        #for session specific volatile data (will not get logged)
        self.vdata = {}

        self.login_attempts = []
        self.socket = socket

    def try_auth(self, type, **kwargs):
        """

        :param username:
        :param password:
        :param auth_type: possible values:
                                plain: plaintext username/password
        :return:
        """
        log_dict = {'timestamp': datetime.utcnow(),
                    'type': type,
                    'id': uuid.uuid4()}

        log_string = ''
        for key, value in kwargs.iteritems():
            log_dict[key] = value
            log_string += '{0}:{1}, '.format(key, value)

        self.login_attempts.append(log_dict)
        logger.debug('{0} authentication attempt from {1}. [{2}] ({3})'
                     .format(self.protocol, self.attacker_ip, log_string.rstrip(', '), self.id))

        if Session.authenticator.try_auth(type, **kwargs):
            self.authenticated = True
            return True
        else:
            return False

    def activity(self):
        self.last_activity = datetime.utcnow()

    def to_dict(self):
        return {
            'hive_id': Session.hive_id,
            'id': self.id,
            'timestamp': self.timestamp,
            'attacker_ip': self.attacker_ip,
            'attacker_source_port': self.attacker_source_port,
            'protocol': self.protocol,
            'honey_ip': self.honey_ip,
            'honey_port': self.honey_port,
            'login_attempts': self.login_attempts,
        }

    def last_activity(self):
        return self.socket.last_update()

    def is_connected(self):
        if self.socket.last_update() > Session.default_timeout:
            logger.debug('Closing session socket due to timeout. ({0})'.format(self.id))
            self.socket.close()
            self.connected = False
        return self.connected