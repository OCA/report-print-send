# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Setting res.company.tech_name in case it is undefined")
    _logger.warning(
        "Please check your server environment configuration to ensure "
        "pingen values are read properly."
    )
    cr.execute(
        """
            UPDATE res_company
            SET tech_name = name
            WHERE tech_name IS NULL;
        """
    )
