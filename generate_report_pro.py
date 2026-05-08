#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import subprocess
from datetime import datetime
from collections import defaultdict

# ==================== 强制 SSH 使用英文路径的密钥 ====================
os.environ['HOME'] = 'D:\\GitHome'
os.environ['GIT_SSH_COMMAND'] = 'C:/Windows/System32/OpenSSH/ssh.exe'

# ==================== 配置 ====================
# 数据目录：根据你的实际绝对路径（已有 football.json 文件夹）
DATA_DIR = r"C:\Users\鼎丰\Desktop\football_report\football.json\2025-26"
OUTPUT_FILE = "output/index.html"

# 联赛名称 -> 数据文件前缀 (en, es, de, it, fr)
LEAGUES = {
    "Premier League": "en",
    "La Liga": "es",
    "Bundesliga": "de",
    "Serie A": "it",
    "Ligue 1": "fr",
}

def get_data_files(prefix):
    """获取指定前缀的所有 JSON 文件（如 en.1.json, en.2.json ...）"""
    files = []
    if not os.path.isdir(DATA_DIR):
        print(f"❌ 数据目录不存在: {DATA_DIR}")
        return files
    for f in os.listdir(DATA_DIR):
        if f.startswith(prefix + ".") and f.endswith(".json"):
            files.append(os.path.join(DATA_DIR, f))
    files.sort(key=lambda x: int(x.split('.')[-2]) if x.split('.')[-2].isdigit() else 0)
    return files

def load_matches_from_file(filepath):
    """解析单个 JSON 文件，返回比赛列表（适配实际结构）"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    matches = []
    for match in data.get("matches", []):
        team1 = match.get("team1")
        team2 = match.get("team2")
        score = match.get("score", {})
        # 优先使用 ft（全场比分）
        ft = score.get("ft")
        if ft and len(ft) == 2:
            score1, score2 = ft[0], ft[1]
        else:
            # 尝试 ht（半场比分）
            ht = score.get("ht")
            if ht and len(ht) == 2:
                score1, score2 = ht[0], ht[1]
            else:
                continue   # 无效比分，跳过
        if team1 and team2 and score1 is not None and score2 is not None:
            matches.append({
                "home": team1,
                "away": team2,
                "home_score": score1,
                "away_score": score2
            })
    return matches

def load_league_data(league_name, prefix):
    """根据前缀加载所有分片文件，合并比赛数据"""
    files = get_data_files(prefix)
    if not files:
        print(f"⚠️ 未找到 {league_name} 的数据文件（前缀 {prefix}）")
        return None
    all_matches = []
    for f in files:
        matches = load_matches_from_file(f)
        all_matches.extend(matches)
    if not all_matches:
        return None
    team_set = set()
    for m in all_matches:
        team_set.add(m["home"])
        team_set.add(m["away"])
    print(f"  加载 {len(all_matches)} 场比赛，{len(team_set)} 支球队")
    return all_matches

def calculate_table(matches):
    """计算积分榜"""
    stats = defaultdict(lambda: {
        "played": 0, "won": 0, "drawn": 0, "lost": 0,
        "goals_for": 0, "goals_against": 0, "points": 0
    })
    for m in matches:
        home = m["home"]
        away = m["away"]
        hg = m["home_score"]
        ag = m["away_score"]

        stats[home]["played"] += 1
        stats[home]["goals_for"] += hg
        stats[home]["goals_against"] += ag
        if hg > ag:
            stats[home]["won"] += 1
            stats[home]["points"] += 3
        elif hg == ag:
            stats[home]["drawn"] += 1
            stats[home]["points"] += 1
        else:
            stats[home]["lost"] += 1

        stats[away]["played"] += 1
        stats[away]["goals_for"] += ag
        stats[away]["goals_against"] += hg
        if ag > hg:
            stats[away]["won"] += 1
            stats[away]["points"] += 3
        elif ag == hg:
            stats[away]["drawn"] += 1
            stats[away]["points"] += 1
        else:
            stats[away]["lost"] += 1

    table = []
    for team, data in stats.items():
        gd = data["goals_for"] - data["goals_against"]
        table.append({
            "team": team,
            "played": data["played"],
            "won": data["won"],
            "drawn": data["drawn"],
            "lost": data["lost"],
            "gf": data["goals_for"],
            "ga": data["goals_against"],
            "gd": gd,
            "points": data["points"]
        })
    table.sort(key=lambda x: (x["points"], x["gd"], x["gf"]), reverse=True)
    for idx, row in enumerate(table, 1):
        row["rank"] = idx
    return table

def generate_html(tables):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    league_tabs = []
    league_panes = []

    for league_name, table in tables.items():
        active_tab = 'active' if not league_tabs else ''
        tab_id = league_name.replace(' ', '_')
        league_tabs.append(f'<li class="nav-item"><button class="nav-link {active_tab}" id="{tab_id}-tab" data-bs-toggle="tab" data-bs-target="#{tab_id}" type="button" role="tab">{league_name}</button></li>')

        rows = ""
        for team in table:
            rows += f"""
            <tr>
                <td>{team['rank']}</td>
                <td class="team-name">{team['team']}</td>
                <td>{team['played']}</td>
                <td>{team['won']}</td>
                <td>{team['drawn']}</td>
                <td>{team['lost']}</td>
                <td>{team['gf']}</td>
                <td>{team['ga']}</td>
                <td>{team['gd']}</td>
                <td><strong>{team['points']}</strong></td>
            </tr>
            """
        pane_active = 'show active' if not league_panes else ''
        league_panes.append(f"""
        <div class="tab-pane fade {pane_active}" id="{tab_id}" role="tabpanel">
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr><th>排名</th><th>球队</th><th>场次</th><th>胜</th><th>平</th><th>负</th><th>进球</th><th>失球</th><th>净胜球</th><th>积分</th></tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚽ 烽域·星舟 · 五大联赛积分榜</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background: #f0f2f5; font-family: 'Segoe UI', Roboto, system-ui; }}
        .container {{ margin-top: 30px; margin-bottom: 30px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #1e3c72; font-weight: 700; }}
        .tab-content {{ background: white; border-radius: 0 0 12px 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .nav-tabs .nav-link {{ font-weight: 600; color: #1e3c72; }}
        .nav-tabs .nav-link.active {{ background-color: #1e3c72; color: white; border-color: #1e3c72; }}
        .table th {{ background-color: #2d3748; color: white; }}
        .team-name {{ font-weight: 600; }}
        footer {{ text-align: center; margin-top: 30px; padding: 15px; color: #718096; border-top: 1px solid #e2e8f0; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>⚽ 烽域·星舟 · 足球数据领航员</h1>
        <p>数据来源：football.json (Public Domain) | 更新：{timestamp}</p>
    </div>
    <ul class="nav nav-tabs" id="leagueTab" role="tablist">
        {''.join(league_tabs)}
    </ul>
    <div class="tab-content" id="leagueTabContent">
        {''.join(league_panes)}
    </div>
    <footer>© 烽域·星舟 | 数据来源：football.json 开源项目</footer>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 报告已生成: {OUTPUT_FILE}")

def git_auto_push():
    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("📭 没有需要提交的变更，跳过提交。")
            return
        commit_msg = f"Auto-update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True, text=True)
        print(f"📦 已提交: {commit_msg}")
        subprocess.run(["git", "push"], check=True, capture_output=True, text=True)
        print("🚀 已推送到远程仓库")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失败: {e}")
        if e.stderr:
            print(e.stderr)

def main():
    print("⚽ 烽域·星舟 积分榜生成器启动")
    # 确保工作目录是脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    tables = {}
    for league_name, prefix in LEAGUES.items():
        print(f"加载 {league_name}...")
        matches = load_league_data(league_name, prefix)
        if matches:
            table = calculate_table(matches)
            tables[league_name] = table
        else:
            tables[league_name] = []
    if not any(tables.values()):
        print("❌ 没有加载到任何联赛数据，请检查 football.json 文件夹路径")
        return
    generate_html(tables)
    git_auto_push()

if __name__ == "__main__":
    main()