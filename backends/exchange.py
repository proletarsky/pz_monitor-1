# backends/exchange

from django.core.mail.backends.base import BaseEmailBackend
import threading
from exchangelib import Credentials, Account, Message, Mailbox
from django.conf import settings


class ExchangeBackend(BaseEmailBackend):
    """
    Class for MS Exchange connectivity and email notification
    """

    def __init__(self, email_user=None, email_password=None, email_account=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self._user = email_user or settings.EMAIL_USER
        self._password = email_password or settings.EMAIL_PASSWORD
        self._account = email_account or settings.EMAIL_ACCOUNT
        self.connection = None
        self._lock = threading.RLock()

    def open(self):
        if self.connection is None:
            try:
                credentials = Credentials(self._user, self._password)
                self.connection = Account(self._account, credentials=credentials, autodiscover=True)
            except Exception as e:
                if not self.fail_silently:
                    raise e
            return True
        else:
            return False

    def close(self):
        if self.connection is not None:
            del self.connection
            self.connection = None

    def send_messages(self, email_messages):
        """
        This function send messages
        :param email_messages: list or tuple of messages
        :return: amount of messages have sent
        """
        if not email_messages:
            return 0
        with self._lock:
            self.open()  # if connection exists open() will do nothing, else it'll open connection
            if self.connection is None:
                return 0  # failed to connect
            # credentials = Credentials(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            # account = Account(settings.EMAIL_ACCOUNT, credentials=credentials, autodiscover=True)
            count = 0
            for m in email_messages:
                try:
                    message = Message(account=self.connection, subject=m.subject,
                                      body=m.body, to_recipients=m.to,
                                      cc_recipients=m.cc)
                    message.send()
                    count += 1
                except Exception as e:
                    if not self.fail_silently:
                        raise e
            return count
