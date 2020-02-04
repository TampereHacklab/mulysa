import django.core.mail.backends.smtp
import logging

logger = logging.getLogger(__name__)


class LoggingBackend(django.core.mail.backends.smtp.EmailBackend):
    """
    Simple email backend based on django default EmailBackend

    Just to get some logging for emails
    """

    def send_messages(self, email_messages):
        try:
            for msg in email_messages:
                logger.info(
                    f"Sending message {msg.subject} to recipients: {msg.to} with body: {msg.body}"
                )
        except Exception as e:
            logger.exception(f"Problem logging recipients {e}")

        return super(LoggingBackend, self).send_messages(email_messages)
