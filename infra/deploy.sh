#!/usr/bin/env bash
# Deploy everything: infrastructure, the API image, and the dashboard.
# Run from the repo root (`make deploy`). Needs Docker, the AWS CLI, Terraform, and Node.
set -euo pipefail

INFRA=infra
tf() { terraform -chdir="$INFRA" "$@"; }
out() { tf output -raw "$1"; }

echo "==> Infrastructure (tables, queue, repository, certificates, dashboard hosting)"
tf init -input=false >/dev/null
tf apply -input=false -auto-approve

echo "==> API image"
repo=$(out ecr_repository_url)
registry=${repo%%/*}
region=$(echo "$registry" | cut -d. -f4)
# Tags are immutable: a new tag every deploy, traceable to its commit.
tag="$(git rev-parse --short HEAD)-$(date +%Y%m%d%H%M%S)"
docker build --platform linux/amd64 --provenance=false -f api/Dockerfile -t "$repo:$tag" .
aws ecr get-login-password --region "$region" | docker login --username AWS --password-stdin "$registry"
docker push "$repo:$tag"

echo "==> API and worker Lambdas on $tag"
# Loaded by every later plan and apply, so they keep the deployed image.
echo "image_tag = \"$tag\"" >"$INFRA/image.auto.tfvars"
tf apply -input=false -auto-approve

echo "==> Dashboard"
# Read outputs here: inside the web/ subshell, -chdir=infra no longer resolves.
api_url=$(out api_url)
cognito_authority=$(out cognito_authority)
cognito_client_id=$(out cognito_client_id)
cognito_domain=$(out cognito_domain)
(
  cd web
  npm ci
  # Demo mode: storm replay and the resident phones. Synthetic data only.
  STATIC_EXPORT=true NEXT_PUBLIC_DEMO_MODE=true NEXT_PUBLIC_API_URL="$api_url"     NEXT_PUBLIC_COGNITO_AUTHORITY="$cognito_authority"     NEXT_PUBLIC_COGNITO_CLIENT_ID="$cognito_client_id"     NEXT_PUBLIC_COGNITO_DOMAIN="$cognito_domain"     npm run build
)
# The export writes route segments as folders (dispatch/__next.dispatch/__PAGE__.txt), but
# the client prefetches them as one dotted name (dispatch/__next.dispatch.__PAGE__.txt).
find web/out -path "*/__next.*/*" -type f | while read -r file; do
  segment=${file%/*}
  cp "$file" "${segment}.${file##*/}"
done
bucket=$(out web_bucket)
# The CLI guesses types from the OS; on Windows .js becomes text/plain and browsers
# refuse to run it. Upload those first with explicit
# types, so no browser or CDN ever caches a script as text/plain; the sync then skips them.
for pair in js:text/javascript mjs:text/javascript css:text/css webp:image/webp   woff2:font/woff2 geojson:application/geo+json svg:image/svg+xml; do
  aws s3 cp web/out "s3://$bucket" --recursive --exclude "*" --include "*.${pair%%:*}"     --content-type "${pair#*:}" --metadata-directive REPLACE --only-show-errors
done
aws s3 sync web/out "s3://$bucket" --delete
aws cloudfront create-invalidation --distribution-id "$(out web_distribution_id)" \
  --paths "/*" --query 'Invalidation.Id' --output text

echo "==> Done: $(out web_url) (API $api_url)"
