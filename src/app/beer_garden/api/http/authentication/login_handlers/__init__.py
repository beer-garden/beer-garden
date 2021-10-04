from .basic import BasicLoginHandler
from .certificate import CertificateLoginHandler

LOGIN_HANDLERS = [BasicLoginHandler, CertificateLoginHandler]
