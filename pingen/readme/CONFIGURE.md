In *Settings \> General Settings \> Pingen*, set for each company:

- the **Client ID** and **Client Secret** of a Pingen API client (Pingen
  app, user profile, *API Access*). The token is requested with the
  `letter` scope only;
- the **Organization ID** (UUID) the letters are billed to;
- the **Address position**: the envelope window (`left` or `right`) where
  the recipient address is printed on the first page of the documents;
- **Staging**: tick it to use the separate staging environment
  (<https://identity-staging.pingen.com>, <https://api-staging.pingen.com>)
  with a staging account; nothing is printed there.

These credentials are only readable by administrators.

Webhooks are configured in the Pingen app, one per event category, all
signed with the **Webhook secret** entered on the company:

- issues: `https://<your-odoo>/pingen/letter_issues`
- sent: `https://<your-odoo>/pingen/sent_letters`
- delivered: `https://<your-odoo>/pingen/delivered_letters`
- undeliverable: `https://<your-odoo>/pingen/undeliverable_letters`

The routes must be reachable from the Internet. A call whose signature does
not match the secret of a company is rejected (HTTP 403).
