#!/usr/bin/env bash
# fix-ci-workflows.sh — Fix pull_request_target vulnerability and switch to GitHub App auth
# across all mountainash-io repos.
#
# Prerequisites:
#   - GitHub App created with contents:read
#   - Org secrets CI_APP_ID and CI_APP_PRIVATE_KEY set
#
# Usage: bash scripts/fix-ci-workflows.sh [--dry-run] [--repo REPO_NAME]

set -euo pipefail

BASE_DIR="/home/nathanielramm/git/mountainash-io/mountainash"
DRY_RUN=false
TARGET_REPO=""
BRANCH_NAME="security/ci-github-app-auth"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --repo) TARGET_REPO="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# All repos with .github/workflows
REPOS=()
for dir in "$BASE_DIR"/*/; do
  repo=$(basename "$dir")
  if [ -d "$dir/.github/workflows" ]; then
    if [ -n "$TARGET_REPO" ] && [ "$repo" != "$TARGET_REPO" ]; then
      continue
    fi
    REPOS+=("$repo")
  fi
done

echo "=== Repos to process: ${#REPOS[@]} ==="
printf '  %s\n' "${REPOS[@]}"
echo

fix_pytest_workflow() {
  local file="$1"
  local repo="$2"
  [ -f "$file" ] || return 0

  echo "  Fixing pytest workflow: $file"

  # 1. pull_request_target -> pull_request
  sed -i 's/pull_request_target:/pull_request:/' "$file"

  # 2. Remove "Get branch name" step block (the whole step)
  # Match from "- name: Get branch name" to the next "- name:" or step
  python3 -c "
import re
with open('$file', 'r') as f:
    content = f.read()

# Remove the 'Get branch name' step
pattern = r'      # Current Branch\n\s*- name: Get branch name\n\s*shell: bash\n\s*run: echo \"BRANCH_NAME=.*\n'
content = re.sub(pattern, '', content)

# Also handle without comment
pattern = r'\s*- name: Get branch name\n\s*shell: bash\n\s*run: echo \"BRANCH_NAME=.*\n'
content = re.sub(pattern, '', content)

with open('$file', 'w') as f:
    f.write(content)
"

  # 3. Remove ref: line from checkout step
  sed -i '/^\s*ref: \${{ env\.BRANCH_NAME }}/d' "$file"

  # 4. Fix fallback branch event name check
  sed -i 's/pull_request_target/pull_request/g' "$file"

  # 4b. Fix target-branch references that used BRANCH_NAME
  # With pull_request trigger, github.head_ref gives the PR branch name
  sed -i 's/target-branch: \${{ env\.BRANCH_NAME }}/target-branch: \${{ github.head_ref }}/g' "$file"

  # 5. Add permissions block if not present
  if ! grep -q '^permissions:' "$file"; then
    sed -i '/^jobs:/i\permissions:\n  contents: read\n' "$file"
  fi

  # 6. Add GitHub App token step before Load/Checkout Dependencies
  if grep -q 'CLONE_PRIVATE_REPOS_TOKEN' "$file" && ! grep -q 'create-github-app-token' "$file"; then
    python3 -c "
import re
with open('$file', 'r') as f:
    content = f.read()

app_token_step = '''      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: \${{ secrets.CI_APP_ID }}
          private-key: \${{ secrets.CI_APP_PRIVATE_KEY }}
          owner: mountainash-io

'''

# Insert before 'Load Dependencies' step if it exists
if '- name: Load Dependencies' in content:
    content = content.replace(
        '      - name: Load Dependencies',
        app_token_step + '      - name: Load Dependencies'
    )
# Or before 'Checkout Dependencies' step
elif '- name: Checkout Dependencies' in content:
    content = content.replace(
        '      - name: Checkout Dependencies',
        app_token_step + '      - name: Checkout Dependencies'
    )

with open('$file', 'w') as f:
    f.write(content)
"
  fi

  # 7. Replace CLONE_PRIVATE_REPOS_TOKEN with app token output
  sed -i 's/\${{ secrets\.CLONE_PRIVATE_REPOS_TOKEN }}/\${{ steps.app-token.outputs.token }}/g' "$file"

  # 8. Remove CODECOV_TOKEN lines (tokenless upload for public repos)
  sed -i '/^\s*token: \${{ secrets\.CODECOV_TOKEN }}/d' "$file"

  # 9. Clean up commented-out dependency checkout blocks
  # (Leave them for now — they're harmless and provide documentation)
}

fix_ruff_workflow() {
  local file="$1"
  [ -f "$file" ] || return 0

  echo "  Fixing ruff workflow: $file"

  sed -i 's/pull_request_target:/pull_request:/' "$file"

  # Remove "Get branch name" step
  python3 -c "
import re
with open('$file', 'r') as f:
    content = f.read()
pattern = r'\s*# Current Branch\n\s*- name: Get branch name\n\s*shell: bash\n\s*run: echo \"BRANCH_NAME=.*\n'
content = re.sub(pattern, '', content)
pattern = r'\s*- name: Get branch name\n\s*shell: bash\n\s*run: echo \"BRANCH_NAME=.*\n'
content = re.sub(pattern, '', content)
with open('$file', 'w') as f:
    f.write(content)
"

  sed -i '/^\s*ref: \${{ env\.BRANCH_NAME }}/d' "$file"

  if ! grep -q '^permissions:' "$file"; then
    sed -i '/^jobs:/i\permissions:\n  contents: read\n' "$file"
  fi
}

fix_radon_workflow() {
  local file="$1"
  [ -f "$file" ] || return 0

  echo "  Fixing radon workflow: $file"

  sed -i 's/pull_request_target:/pull_request:/' "$file"

  python3 -c "
import re
with open('$file', 'r') as f:
    content = f.read()
pattern = r'\s*# Current Branch\n\s*- name: Get branch name\n\s*shell: bash\n\s*run: echo \"BRANCH_NAME=.*\n'
content = re.sub(pattern, '', content)
pattern = r'\s*- name: Get branch name\n\s*shell: bash\n\s*run: echo \"BRANCH_NAME=.*\n'
content = re.sub(pattern, '', content)
with open('$file', 'w') as f:
    f.write(content)
"

  sed -i '/^\s*ref: \${{ env\.BRANCH_NAME }}/d' "$file"

  if ! grep -q '^permissions:' "$file"; then
    sed -i '/^jobs:/i\permissions:\n  contents: read\n' "$file"
  fi
}

fix_build_workflow() {
  local file="$1"
  [ -f "$file" ] || return 0

  echo "  Fixing build workflow: $file"

  # Add app token step if using CLONE_PRIVATE_REPOS_TOKEN
  if grep -q 'CLONE_PRIVATE_REPOS_TOKEN' "$file" && ! grep -q 'create-github-app-token' "$file"; then
    python3 -c "
with open('$file', 'r') as f:
    content = f.read()

# Find the first usage of CLONE_PRIVATE_REPOS_TOKEN and add token gen before its job steps
# This is trickier for build workflows — they may have multiple jobs
# For now, replace the secret reference and add the step at the beginning of each job's steps

app_token_step = '''      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: \${{ secrets.CI_APP_ID }}
          private-key: \${{ secrets.CI_APP_PRIVATE_KEY }}
          owner: mountainash-io

'''

# Insert after the first 'steps:' line in the build job
import re
# Find 'steps:' and insert after it
content = re.sub(
    r'(    steps:\n)',
    r'\1' + app_token_step,
    content,
    count=1
)

with open('$file', 'w') as f:
    f.write(content)
"
    sed -i 's/\${{ secrets\.CLONE_PRIVATE_REPOS_TOKEN }}/\${{ steps.app-token.outputs.token }}/g' "$file"
  fi

  # Fix target-branch references
  sed -i 's/target-branch: \${{ env\.BRANCH_NAME }}/target-branch: \${{ github.head_ref }}/g' "$file"

  # Ensure permissions include contents: write for build workflows
  if ! grep -q '^permissions:' "$file"; then
    sed -i '/^jobs:/i\permissions:\n  contents: write\n  pull-requests: read\n' "$file"
  fi
}

fix_release_deps_workflow() {
  local file="$1"
  [ -f "$file" ] || return 0

  echo "  Fixing release deps workflow: $file"

  if grep -q 'CLONE_PRIVATE_REPOS_TOKEN' "$file" && ! grep -q 'create-github-app-token' "$file"; then
    python3 -c "
with open('$file', 'r') as f:
    content = f.read()

app_token_step = '''      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: \${{ secrets.CI_APP_ID }}
          private-key: \${{ secrets.CI_APP_PRIVATE_KEY }}
          owner: mountainash-io

'''

if '- name: Load Dependencies' in content:
    content = content.replace(
        '      - name: Load Dependencies',
        app_token_step + '      - name: Load Dependencies'
    )
elif '- name: Checkout Dependencies' in content:
    content = content.replace(
        '      - name: Checkout Dependencies',
        app_token_step + '      - name: Checkout Dependencies'
    )

with open('$file', 'w') as f:
    f.write(content)
"
    sed -i 's/\${{ secrets\.CLONE_PRIVATE_REPOS_TOKEN }}/\${{ steps.app-token.outputs.token }}/g' "$file"
  fi

  if ! grep -q '^permissions:' "$file"; then
    sed -i '/^jobs:/i\permissions:\n  contents: read\n' "$file"
  fi
}

fix_main_release_validation() {
  local file="$1"
  [ -f "$file" ] || return 0

  echo "  Fixing main release validation: $file"

  if grep -q 'CLONE_PRIVATE_REPOS_TOKEN' "$file" && ! grep -q 'create-github-app-token' "$file"; then
    python3 -c "
with open('$file', 'r') as f:
    content = f.read()

app_token_step = '''      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: \${{ secrets.CI_APP_ID }}
          private-key: \${{ secrets.CI_APP_PRIVATE_KEY }}
          owner: mountainash-io

'''

if '- name: Load Dependencies' in content:
    content = content.replace(
        '      - name: Load Dependencies',
        app_token_step + '      - name: Load Dependencies'
    )

with open('$file', 'w') as f:
    f.write(content)
"
    sed -i 's/\${{ secrets\.CLONE_PRIVATE_REPOS_TOKEN }}/\${{ steps.app-token.outputs.token }}/g' "$file"
  fi
}

for repo in "${REPOS[@]}"; do
  repo_dir="$BASE_DIR/$repo"
  echo "=== Processing: $repo ==="

  # Check if there's anything to fix
  needs_fix=false
  if grep -rq 'pull_request_target' "$repo_dir/.github/" 2>/dev/null; then
    needs_fix=true
  fi
  if grep -rq 'CLONE_PRIVATE_REPOS_TOKEN' "$repo_dir/.github/" 2>/dev/null; then
    needs_fix=true
  fi

  if [ "$needs_fix" = false ]; then
    echo "  Already fixed, skipping."
    echo
    continue
  fi

  if [ "$DRY_RUN" = true ]; then
    echo "  [DRY RUN] Would fix:"
    grep -rn 'pull_request_target\|CLONE_PRIVATE_REPOS_TOKEN' "$repo_dir/.github/" 2>/dev/null || true
    echo
    continue
  fi

  # Create branch
  cd "$repo_dir"

  # Ensure we're on develop (or main if no develop)
  default_branch=$(git branch -a 2>/dev/null | grep -oP '(develop|main)' | head -1 || echo "main")
  git checkout "$default_branch" 2>/dev/null || true
  git pull origin "$default_branch" 2>/dev/null || true

  # Check if branch already exists
  if git branch --list "$BRANCH_NAME" | grep -q .; then
    echo "  Branch $BRANCH_NAME already exists, checking it out"
    git checkout "$BRANCH_NAME"
  else
    git checkout -b "$BRANCH_NAME"
  fi

  # Apply fixes
  fix_pytest_workflow "$repo_dir/.github/workflows/python-run-pytest.yml" "$repo"
  fix_ruff_workflow "$repo_dir/.github/workflows/python-run-ruff.yml"
  fix_radon_workflow "$repo_dir/.github/workflows/python-run-radon.yml"
  fix_build_workflow "$repo_dir/.github/workflows/build-and-release-package.yml"
  fix_release_deps_workflow "$repo_dir/.github/workflows/main-release-build-dependencies.yml"
  fix_main_release_validation "$repo_dir/.github/workflows/main-release-branch-validation.yml"

  # Check if there are changes
  if git diff --quiet && git diff --cached --quiet; then
    echo "  No changes needed."
    git checkout "$default_branch" 2>/dev/null || true
  else
    echo "  Changes made, committing..."
    git add .github/
    git commit -m "$(cat <<'EOF'
security(ci): fix pull_request_target vulnerability, switch to GitHub App auth

- Switch pull_request_target → pull_request (prevents fork PRs from
  accessing repo secrets)
- Add explicit permissions: contents: read
- Replace CLONE_PRIVATE_REPOS_TOKEN PAT with ephemeral GitHub App token
  via actions/create-github-app-token@v2
- Remove manual GITHUB_HEAD_REF checkout (use default merge commit)
- Remove CODECOV_TOKEN (public repos use tokenless OIDC upload)

Requires org secrets CI_APP_ID and CI_APP_PRIVATE_KEY to be configured.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
    )"
    echo "  Committed."
  fi

  cd "$BASE_DIR/mountainash"
  echo
done

echo "=== Done ==="
echo
echo "Next steps:"
echo "1. Create the GitHub App and set org secrets (CI_APP_ID, CI_APP_PRIVATE_KEY)"
echo "2. Review changes in each repo"
echo "3. Push branches and create PRs:"
echo "   for repo in ${REPOS[*]}; do"
echo "     cd $BASE_DIR/\$repo"
echo "     git push -u origin $BRANCH_NAME"
echo "     gh pr create --base develop --title 'security(ci): fix pull_request_target, switch to GitHub App auth' --body '...'"
echo "   done"
