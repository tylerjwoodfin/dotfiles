#!/bin/zsh
# Script to import docker and backend repos into Gitea with full history

set -e

GITEA_URL="http://localhost:3005"
GITEA_USER="tyler"
GITEA_PASSWORD="${GITEA_PASSWORD:-}"  # Set this or it will prompt
RAINBOW_IP="${RAINBOW_IP:-38.102.87.250}"
OLD_GITEA_URL="http://${RAINBOW_IP}:3005"  # Adjust if different

REPOS=("docker" "backend")
ORG="voice2749"

echo "🔧 Importing repositories into Gitea..."

# Function to create repo in Gitea via API
create_gitea_repo() {
    local repo_name=$1
    local description=$2
    
    echo "Creating repository: ${ORG}/${repo_name}"
    
    # Get CSRF token
    CSRF_TOKEN=$(curl -s -c /tmp/gitea_cookies.txt "${GITEA_URL}/user/login" | grep -oP 'name="_csrf" value="\K[^"]+')
    
    # Login to get session
    curl -s -b /tmp/gitea_cookies.txt -c /tmp/gitea_cookies.txt \
        -X POST "${GITEA_URL}/user/login" \
        -d "_csrf=${CSRF_TOKEN}" \
        -d "user_name=${GITEA_USER}" \
        -d "password=${GITEA_PASSWORD}" \
        -d "remember_me=on" > /dev/null
    
    # Create repository
    curl -s -b /tmp/gitea_cookies.txt -c /tmp/gitea_cookies.txt \
        -X POST "${GITEA_URL}/api/v1/orgs/${ORG}/repos" \
        -H "Content-Type: application/json" \
        -H "Authorization: token ${GITEA_TOKEN:-}" \
        -d "{
            \"name\": \"${repo_name}\",
            \"description\": \"${description}\",
            \"private\": false,
            \"auto_init\": false
        }" || {
        echo "⚠️  Repository might already exist, continuing..."
    }
    
    rm -f /tmp/gitea_cookies.txt
}

# Function to clone and push repo
import_repo() {
    local repo_name=$1
    local repo_path="${HOME}/git/${repo_name}"
    local temp_clone="/tmp/gitea_import_${repo_name}"
    
    echo ""
    echo "📦 Importing ${repo_name}..."
    
    # Option 1: Try to clone from old Gitea
    if [ -n "${OLD_GITEA_URL}" ] && [ "${OLD_GITEA_URL}" != "http://:3005" ]; then
        echo "  Attempting to clone from old Gitea: ${OLD_GITEA_URL}"
        rm -rf "${temp_clone}"
        if git clone "ssh://git@${RAINBOW_IP}:222/${ORG}/${repo_name}.git" "${temp_clone}" 2>/dev/null; then
            echo "  ✅ Cloned from old Gitea"
            cd "${temp_clone}"
        else
            echo "  ⚠️  Could not clone from old Gitea, trying local repo"
            cd "${repo_path}"
        fi
    else
        # Option 2: Use local repo and try to fetch from old remote
        cd "${repo_path}"
        if git remote get-url origin 2>/dev/null | grep -q "${RAINBOW_IP}"; then
            echo "  Fetching from old Gitea remote..."
            git fetch origin --all --tags 2>/dev/null || echo "  ⚠️  Could not fetch from old remote"
        fi
    fi
    
    # Ensure we have the new Gitea remote
    git remote remove new_origin 2>/dev/null || true
    git remote add new_origin "ssh://git@192.168.1.101:222/${ORG}/${repo_name}.git" 2>/dev/null || \
        git remote set-url origin "ssh://git@192.168.1.101:222/${ORG}/${repo_name}.git"
    
    # Get all branches
    BRANCHES=$(git branch -r | grep -v HEAD | sed 's|origin/||' | xargs)
    if [ -z "${BRANCHES}" ]; then
        BRANCHES="main master"
    fi
    
    # Push all branches and tags
    echo "  Pushing branches and tags to new Gitea..."
    for branch in ${BRANCHES}; do
        if git show-ref --verify --quiet "refs/heads/${branch}" || git show-ref --verify --quiet "refs/remotes/origin/${branch}"; then
            echo "    Pushing branch: ${branch}"
            git checkout -b "${branch}" "origin/${branch}" 2>/dev/null || git checkout "${branch}" 2>/dev/null || true
            git push -u origin "${branch}" --force 2>/dev/null || git push -u new_origin "${branch}" --force 2>/dev/null || true
        fi
    done
    
    # Push all tags
    git push origin --tags --force 2>/dev/null || git push new_origin --tags --force 2>/dev/null || true
    
    # Cleanup temp clone
    if [ -d "${temp_clone}" ]; then
        rm -rf "${temp_clone}"
    fi
    
    echo "  ✅ ${repo_name} imported"
}

# Main execution
echo "This script will:"
echo "  1. Create repositories in Gitea (if they don't exist)"
echo "  2. Import full git history from old Gitea or local repos"
echo "  3. Push everything to the new Gitea"
echo ""

if [ -z "${GITEA_PASSWORD}" ] && [ -z "${GITEA_TOKEN}" ]; then
    echo "⚠️  Note: GITEA_PASSWORD or GITEA_TOKEN not set."
    echo "   Repositories might need to be created manually in Gitea UI first."
    echo "   Or set GITEA_PASSWORD environment variable."
    echo ""
fi

for repo in "${REPOS[@]}"; do
    if [ -n "${GITEA_PASSWORD}" ] || [ -n "${GITEA_TOKEN}" ]; then
        create_gitea_repo "${repo}" "Restored ${repo} repository"
    fi
    import_repo "${repo}"
done

echo ""
echo "✅ Repository import complete!"
echo ""
echo "Next steps:"
echo "  1. Verify repositories in Gitea UI: ${GITEA_URL}"
echo "  2. Check that all branches and history are present"
echo "  3. Update local remotes if needed:"
echo "     cd ~/git/docker && git remote set-url origin ssh://git@192.168.1.101:222/${ORG}/docker.git"
echo "     cd ~/git/backend && git remote set-url origin ssh://git@192.168.1.101:222/${ORG}/backend.git"


