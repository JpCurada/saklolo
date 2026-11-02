# Dispatcher sign-in. Invite-only: an admin creates each account (infra/README.md).
# The API accepts Cognito access tokens from members of the `dispatchers` group.

locals {
  dashboard_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "https://${var.web_domain}"]
}

resource "aws_cognito_user_pool" "dispatchers" {
  name                = "${local.name_prefix}-dispatchers"
  deletion_protection = "INACTIVE"

  # The username becomes the name in each case's history, so admins pick a readable one.
  alias_attributes         = ["email"]
  auto_verified_attributes = ["email"]

  username_configuration {
    case_sensitive = false
  }

  admin_create_user_config {
    allow_admin_create_user_only = true

    invite_message_template {
      email_subject = "Your Saklolo dispatcher account"
      email_message = "You can now sign in to the Saklolo dispatch dashboard. Username: {username} Temporary password: {####} You will choose a new password at first sign-in."
      sms_message   = "Saklolo dispatcher invite. Username: {username} Temporary password: {####}"
    }
  }

  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }
}

resource "aws_cognito_user_group" "dispatchers" {
  name         = "dispatchers"
  user_pool_id = aws_cognito_user_pool.dispatchers.id
  description  = "Can read cases and assign, override, and close them"
}

# A public browser client: authorization code with PKCE, no secret.
resource "aws_cognito_user_pool_client" "dashboard" {
  name         = "${local.name_prefix}-dashboard"
  user_pool_id = aws_cognito_user_pool.dispatchers.id

  generate_secret                      = false
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO"]
  explicit_auth_flows                  = ["ALLOW_REFRESH_TOKEN_AUTH"] # sign-in is on the hosted page
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation              = true

  callback_urls = [for origin in local.dashboard_origins : "${origin}/auth/callback"]
  logout_urls   = [for origin in local.dashboard_origins : "${origin}/"]

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 7
  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}

resource "aws_cognito_user_pool_domain" "hosted_ui" {
  domain                = var.cognito_domain_prefix
  user_pool_id          = aws_cognito_user_pool.dispatchers.id
  managed_login_version = 2
}

resource "aws_cognito_managed_login_branding" "dashboard" {
  user_pool_id                = aws_cognito_user_pool_domain.hosted_ui.user_pool_id
  client_id                   = aws_cognito_user_pool_client.dashboard.id
  use_cognito_provided_values = true

  lifecycle {
    ignore_changes = [settings, asset, use_cognito_provided_values]
  }
}
