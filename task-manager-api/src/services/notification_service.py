"""Envio de notificações por e-mail.

Correções em relação a `services/notification_service.py`:

- As credenciais SMTP saíram do código para a configuração. Host, usuário e
  senha (`senha123`) estavam fixos no arquivo, versionados no Git.
- `smtplib.SMTP(host, port)` não tinha `timeout`: um servidor que não
  respondesse pendurava o worker indefinidamente.
- `print()` deu lugar a `logging`.
- A lista `self.notifications` em memória saiu. Era estado por processo:
  perdido em restart e divergente entre workers, então `get_notifications`
  devolvia resultados diferentes conforme quem atendia a requisição.
  Persistir notificações exige uma tabela nova — fora do escopo desta
  refatoração, e nenhum endpoint as expunha.

Nota: este módulo continua sem ser chamado por nenhum endpoint, exatamente
como no original. Ele foi mantido porque o envio é assíncrono por natureza e
remover a capacidade seria uma decisão de produto, não de refatoração.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, smtp_settings):
        self._smtp = smtp_settings

    def send_email(self, to, subject, body):
        """Envia o e-mail. Devolve `False` em falha, sem propagar exceção."""
        if not self._smtp.is_configured:
            logger.info(
                "SMTP não configurado; e-mail para %s apenas registrado: %s",
                to,
                subject,
            )
            return False

        message = EmailMessage()
        message["From"] = self._smtp.user
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(
                self._smtp.host, self._smtp.port, timeout=self._smtp.timeout
            ) as server:
                if self._smtp.use_tls:
                    server.starttls()
                server.login(self._smtp.user, self._smtp.password)
                server.send_message(message)
        except (OSError, smtplib.SMTPException):
            # Notificação é acessório: a falha é logada e não derruba a
            # operação de negócio que a disparou.
            logger.exception("Falha ao enviar e-mail para %s", to)
            return False

        logger.info("E-mail enviado para %s", to)
        return True

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\n"
            f"Status: {task.status}"
        )
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        return self.send_email(user.email, subject, body)
