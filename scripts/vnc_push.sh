#!/bin/bash
# Federal Contract Sniper — VNC Git Push Wrapper
# Multi-route failfast parallel push to GitHub

PROJECT="/mnt/agents/output/federal-contract-sniper"
PAT="***REDACTED***"
REPO="toxicwind/federal-contract-sniper"
LOG="$PROJECT/outputs/run/git_push_vnc_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$PROJECT/outputs/run"

echo "[VNC-PUSH] Starting multi-route failfast push"
echo "[VNC-PUSH] Log: $LOG"

(
    cd "$PROJECT"

    # Git config
    git config --global --add safe.directory '*' 2>/dev/null
    git config --global user.name 'toxicwind' 2>/dev/null
    git config --global user.email 'toxicwind@users.noreply.github.com' 2>/dev/null

    # Stage and commit
    git add .
    git commit -m "v4.0 update: $(date -Iseconds)" 2>/dev/null || true

    # Route 1: Git HTTPS push
    echo "[VNC-PUSH] Route 1: git HTTPS..."
    git remote remove origin 2>/dev/null
    git remote add origin "https://${PAT}@github.com/${REPO}.git" 2>/dev/null
    if git push -u origin main --force 2>/dev/null; then
        echo "[VNC-PUSH] Route 1 SUCCESS"
        exit 0
    fi

    # Route 2: Git with explicit user:pass
    echo "[VNC-PUSH] Route 2: git user:pass..."
    git remote remove origin 2>/dev/null
    git remote add origin "https://toxicwind:${PAT}@github.com/${REPO}.git" 2>/dev/null
    if git push -u origin main --force 2>/dev/null; then
        echo "[VNC-PUSH] Route 2 SUCCESS"
        exit 0
    fi

    # Route 3: GitHub API fallback
    echo "[VNC-PUSH] Route 3: GitHub API sync..."
    python3 -c "
import os,subprocess as sp,json,base64,sys
PAT='$PAT'
REPO='$REPO'
PROJECT='$PROJECT'

# Get base commit
r = sp.run(['curl','-s','-H',f'Authorization: token {PAT}',f'https://api.github.com/repos/{REPO}/git/refs/heads/main'],capture_output=True,text=True,timeout=15)
try:
    ref = json.loads(r.stdout)
    base_sha = ref['object']['sha']
except:
    print('API: failed to get base sha'); sys.exit(1)

# Get base tree
r2 = sp.run(['curl','-s','-H',f'Authorization: token {PAT}',f'https://api.github.com/repos/{REPO}/git/commits/{base_sha}'],capture_output=True,text=True,timeout=15)
try:
    commit = json.loads(r2.stdout)
    base_tree = commit['tree']['sha']
except:
    print('API: failed to get tree'); sys.exit(1)

# Build tree items
tree_items = []
for root,dirs,files in os.walk(PROJECT):
    if any(x in root for x in ['/.git','/outputs/','/__pycache__']):
        continue
    for f in files:
        if f == '.gitkeep':
            continue
        fp = os.path.join(root,f)
        rel = os.path.relpath(fp, PROJECT)
        try:
            with open(fp,'rb') as fh:
                content = fh.read().decode('utf-8',errors='replace')
        except:
            continue
        tree_items.append({'path':rel,'mode':'100644','type':'blob','content':content})

# Create tree (batch in groups of 50)
all_items = tree_items
batch_size = 50
new_tree_sha = base_tree
for i in range(0,len(all_items),batch_size):
    batch = all_items[i:i+batch_size]
    payload = json.dumps({'base_tree':new_tree_sha,'tree':batch})
    r3 = sp.run(['curl','-s','-X','POST','-H',f'Authorization: token {PAT}','-H','Content-Type: application/json',f'https://api.github.com/repos/{REPO}/git/trees','-d',payload],capture_output=True,text=True,timeout=30)
    try:
        tree_data = json.loads(r3.stdout)
        new_tree_sha = tree_data['sha']
    except:
        print(f'API: tree batch {i} failed'); break

# Create commit
payload = json.dumps({'message':f'v4.0 update via API: {os.popen(\"date -Iseconds\").read().strip()}','tree':new_tree_sha,'parents':[base_sha]})
r4 = sp.run(['curl','-s','-X','POST','-H',f'Authorization: token {PAT}','-H','Content-Type: application/json',f'https://api.github.com/repos/{REPO}/git/commits','-d',payload],capture_output=True,text=True,timeout=20)
try:
    new_commit = json.loads(r4.stdout)['sha']
except:
    print('API: commit failed'); sys.exit(1)

# Update ref
payload = json.dumps({'sha':new_commit,'force':True})
r5 = sp.run(['curl','-s','-X','PATCH','-H',f'Authorization: token {PAT}','-H','Content-Type: application/json',f'https://api.github.com/repos/{REPO}/git/refs/heads/main','-d',payload],capture_output=True,text=True,timeout=20)
if '\"sha\"' in r5.stdout:
    print('API: SUCCESS')
else:
    print('API: ref update failed')
    sys.exit(1)
" 2>/dev/null && echo "[VNC-PUSH] Route 3 SUCCESS" && exit 0

    echo "[VNC-PUSH] ALL ROUTES FAILED"
    exit 1
) > "$LOG" 2>&1 &

PID=$!
echo "$PID" > "$PROJECT/outputs/run/.pid_git_push"
echo "[VNC-PUSH] Detached PID: $PID"
disown $PID 2>/dev/null || true

sleep 2
if kill -0 "$PID" 2>/dev/null; then
    echo "[VNC-PUSH] SUCCESS: PID $PID running detached"
else
    echo "[VNC-PUSH] WARNING: PID exited quickly (check $LOG)"
fi

echo "[VNC-PUSH] To monitor: tail -f $LOG"
echo "[VNC-PUSH] To kill: kill $(cat $PROJECT/outputs/run/.pid_git_push 2>/dev/null)"
