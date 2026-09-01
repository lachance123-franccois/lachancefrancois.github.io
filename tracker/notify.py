"""
Notification par email.

Correction principale : le mot de passe d'application iCloud était écrit en
clair dans le fichier précédent (`password="…"` dans le bloc `__main__`). Les
identifiants viennent maintenant exclusivement de l'environnement, ce qui les
rend compatibles avec les secrets GitHub Actions et impossibles à committer
par accident.

Autres corrections :
- Version texte en plus du HTML. Un message uniquement HTML est très souvent
  classé en indésirable, ce qui explique bien des « notifications jamais
  reçues ».
- Échappement des contenus : un titre d'annonce contenant `<` ou `&` cassait
  le HTML du message.
- Les liens « Gérer mes préférences » et « Se désabonner » pointaient vers
  `francois-tracker.fr`, un domaine qui n'existe pas. Retirés : un digest que
  l'on s'envoie à soi-même n'a pas besoin de lien de désabonnement.
"""

from __future__ import annotations

import html
import logging
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

LABELS = {
    "phd": "Thèses",
    "internship": "Stages",
    "housing": "Logements",
}


class MissingCredentials(RuntimeError):
    pass


class Mailer:
    def __init__(self, host: str, port: int, user: str, password: str,
                 sender: Optional[str] = None):
        if not all([host, port, user, password]):
            raise MissingCredentials(
                "Identifiants SMTP incomplets. Définir SMTP_HOST, SMTP_PORT, "
                "SMTP_USER et SMTP_PASSWORD dans l'environnement."
            )
        self.host, self.port = host, int(port)
        self.user, self.password = user, password
        self.sender = sender or user

    @classmethod
    def from_env(cls) -> "Mailer":
        return cls(
            host=os.environ.get("SMTP_HOST", ""),
            port=os.environ.get("SMTP_PORT", "587"),
            user=os.environ.get("SMTP_USER", ""),
            password=os.environ.get("SMTP_PASSWORD", ""),
            sender=os.environ.get("SMTP_SENDER"),
        )

    def send_digest(self, recipient: str, offers: List[dict]) -> bool:
        if not offers:
            logger.info("aucune offre à notifier")
            return True

        grouped: Dict[str, List[dict]] = {}
        for offer in offers:
            grouped.setdefault(offer["kind"], []).append(offer)

        msg = EmailMessage()
        msg["Subject"] = f"Veille — {len(offers)} nouvelle(s) offre(s) · {date.today():%d/%m/%Y}"
        msg["From"] = self.sender
        msg["To"] = recipient
        msg.set_content(_plain_digest(grouped))
        msg.add_alternative(_html_digest(grouped), subtype="html")

        try:
            with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
        except smtplib.SMTPAuthenticationError:
            logger.error(
                "authentification SMTP refusée. Sur iCloud et Gmail, il faut "
                "un mot de passe d'application, pas le mot de passe du compte."
            )
            return False
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("envoi impossible : %s", exc)
            return False

        logger.info("digest envoyé à %s (%d offres)", recipient, len(offers))
        return True


def _plain_digest(grouped: Dict[str, List[dict]]) -> str:
    lines = [f"Veille du {date.today():%d/%m/%Y}", ""]
    for kind, items in grouped.items():
        lines.append(f"{LABELS.get(kind, kind).upper()} ({len(items)})")
        lines.append("-" * 40)
        for offer in items:
            lines.append(offer["title"])
            meta = " · ".join(
                str(x) for x in (offer.get("organisation"), offer.get("location"),
                                 f"{offer['price']:.0f} €" if offer.get("price") else None)
                if x
            )
            if meta:
                lines.append(f"  {meta}")
            lines.append(f"  {offer['url']}")
            lines.append("")
    return "\n".join(lines)


def _html_digest(grouped: Dict[str, List[dict]]) -> str:
    def esc(value) -> str:
        return html.escape(str(value or ""), quote=True)

    sections = []
    for kind, items in grouped.items():
        cards = []
        for offer in items:
            meta_parts = [
                esc(offer.get("organisation")),
                esc(offer.get("location")),
                f"{offer['price']:.0f}&nbsp;€" if offer.get("price") else "",
                esc(offer.get("source")),
            ]
            meta = " &middot; ".join(p for p in meta_parts if p)
            keywords = "".join(
                f'<span style="display:inline-block;font:500 11px monospace;'
                f'color:#177984;border:1px solid #cfe0e2;border-radius:99px;'
                f'padding:2px 8px;margin:0 4px 4px 0;">{esc(k)}</span>'
                for k in (offer.get("keywords") or [])[:5]
            )
            cards.append(f"""
      <tr><td style="padding:14px 0;border-bottom:1px solid #e3e8ea;">
        <a href="{esc(offer['url'])}" style="font:600 15px/1.35 -apple-system,Segoe UI,sans-serif;color:#10202e;text-decoration:none;">{esc(offer['title'])}</a>
        <div style="font:400 12px/1.6 -apple-system,Segoe UI,sans-serif;color:#5b7280;margin-top:3px;">{meta}</div>
        <div style="margin-top:7px;">{keywords}</div>
      </td></tr>""")

        sections.append(f"""
    <tr><td style="padding-top:26px;">
      <div style="font:600 13px -apple-system,Segoe UI,sans-serif;color:#177984;
                  border-bottom:2px solid #1f9aa8;padding-bottom:5px;">
        {esc(LABELS.get(kind, kind))} — {len(items)}
      </div>
      <table width="100%" cellpadding="0" cellspacing="0">{''.join(cards)}</table>
    </td></tr>""")

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"></head>
<body style="margin:0;padding:24px;background:#f6f7f5;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#fff;border:1px solid #dfe4e6;border-radius:12px;padding:28px;">
        <tr><td style="font:600 18px -apple-system,Segoe UI,sans-serif;color:#10202e;">
          Veille du {date.today():%d/%m/%Y}
        </td></tr>
        {''.join(sections)}
        <tr><td style="padding-top:28px;font:400 11px -apple-system,Segoe UI,sans-serif;color:#8296a0;">
          Digest généré automatiquement par Academic Tracker.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""