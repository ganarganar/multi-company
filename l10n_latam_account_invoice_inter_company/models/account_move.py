##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import models, _
from odoo.exceptions import UserError
from odoo.tests.common import Form

class AccountMove(models.Model):

    _inherit = "account.move"

    def _prepare_invoice_data(self, dest_company):
        """ We override the entire function because it seems that
        writing currency_id is not allowed when account_ux is installed.
        Also, we add the l10n_latam fields data.
        """
        self.ensure_one()
        dest_inv_type = self._get_destination_invoice_type()
        dest_journal_type = self._get_destination_journal_type()
        # Find the correct journal
        # If origin journal uses documents, then search a destiny journal that uses documents.
        if self.journal_id.l10n_latam_use_documents:
            dest_journal = self.env["account.journal"].search(
            [("type", "=", dest_journal_type), ("company_id", "=", dest_company.id), ("l10n_latam_use_documents", "=", True)],
            limit=1,
            )
            if not dest_journal:
                raise UserError(
                    _("Please define %s journal for this company: '%s' (id:%d).")
                    % (dest_journal_type, dest_company.name, dest_company.id)
                )
        else:
            dest_journal = self.env["account.journal"].search(
                [("type", "=", dest_journal_type), ("company_id", "=", dest_company.id), ("l10n_latam_use_documents", "=", False)],
                limit=1,
            )
            if not dest_journal:
                raise UserError(
                    _("Please define %s journal without documents for this company: '%s' (id:%d).")
                    % (dest_journal_type, dest_company.name, dest_company.id)
                )
        # Use test.Form() class to trigger propper onchanges on the invoice
        dest_invoice_data = Form(
            self.env["account.move"].with_context(
                default_type=dest_inv_type, force_company=dest_company.id
            )
        )
        dest_invoice_data.journal_id = dest_journal
        dest_invoice_data.partner_id = self.company_id.partner_id
        dest_invoice_data.ref = self.name
        dest_invoice_data.invoice_date = self.invoice_date
        dest_invoice_data.narration = self.narration
        # Here we've deleted currency_id as it's not compatible with account_ux
        # Also we've added l10n_latam_document_number
        dest_invoice_data.l10n_latam_document_number = self.l10n_latam_document_number
        vals = dest_invoice_data._values_to_save(all_fields=True)
        vals.update(
            {
                "invoice_origin": _("%s - Invoice: %s")
                % (self.company_id.name, self.name),
                "auto_invoice_id": self.id,
                "auto_generated": True,
            }
        )
        return vals
