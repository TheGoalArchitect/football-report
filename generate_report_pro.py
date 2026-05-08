#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import subprocess
from datetime import datetime
from collections import defaultdict

# ==================== 强制 SSH 使用英文路径的密钥 ====================
os.environ['HOME'] = 'D:\\GitHome'          # 与 setx HOME 设置的路径一致
os.environ['GIT_SSH_COMMAND'] = 'C:/Windows/System32/OpenSSH/ssh.exe'

# ==================== 配置 ====================
DATA_ROOT = "football.json/2025-26"         # 数据文件夹位置
OUTPUT_FILE = "output/index.html"
LEAGUES = {
    "Premier League": "england",
    "La Liga": "spain",
    "Bundesliga": "germany",
    "Serie A": "italy",
    "Ligue 1": "france",
}

# ==================== 积分榜计算函数 ====================
def calculate_table(matches):
    """根据比赛列表计算积分榜
    输入: matches = [{"home": "Team A", "away": "Team B", "home_score": 2, "away_score": 1}, ...]
    输出: 列表 of dict，按积分、净胜球、进球排序
    """
    stats = defaultdict(lambda: {
        "played": 0, "won": 0, "drawn": 0, "lost": 0,
        "goals_for": 0, "goals_against": 0, "points": 0
    })

    for m in matches:
        home = m["home"]
        away = m["away"]
        hg = m["home_score"]
        ag = m["away_score"]

        # 更新主队
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

        # 更新客队
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

    # 转换为列表并计算净胜球
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

    # 排序：积分 > 净胜球 > 进球数
    table.sort(key=lambda x: (x["points"], x["gd"], x["gf"]), reverse=True)
    # 添加排名
    for idx, row in enumerate(table, 1):
        row["rank"] = idx
    return table

# ==================== 加载联赛数据 ====================
def load_league_data(league_name, folder_name):
    file_path = os.path.join(DATA_ROOT, folder_name, "matches.json")
    if not os.path.exists(file_path):
        print(f"⚠️ 未找到数据文件: {file_path}")
        return None, None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = []
    for match in data.get("matches", []):
        # 适配不同的 JSON 结构（football.json 常见格式）
        # 有的直接是 {"home": ..., "away": ..., "home_score": ..., "away_score": ...}
        # 有的是嵌套在 "score" 里，我们做兼容处理
        home_team = match.get("home", {}).get("team_name") or match.get("home_team", {}).get("name")
        away_team = match.get("away", {}).get("team_name") or match.get("away_team", {}).get("name")
        if not home_team or not away_team:
            continue

        # 尝试多种得分字段
        if "home_score" in match and "away_score" in match:
            hs = match["home_score"]
            as_ = match["away_score"]
        elif "score" in match:
            hs = match["score"].get("home", 0)
            as_ = match["score"].get("away", 0)
        else:
            continue

        matches.append({
            "home": home_team,
            "away": away_team,
            "home_score": hs,
            "away_score": as_
        })

    print(f"  加载 {len(matches)} 场比赛，{len(set(m['home'] for m in matches) | set(m['away'] for m in matches))} 支球队")
    return matches, league_name

# ==================== 生成 HTML ====================
def generate_html(tables):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建每个联赛的表格 HTML
    league_tabs = []
    league_panes = []

    for league_name, table in tables.items():
        # 生成 tab 按钮
        active_tab = 'active' if not league_tabs else ''
        tab_id = league_name.replace(' ', '_')
        league_tabs.append(f'<li class="nav-item" role="presentation"><button class="nav-link {active_tab}" id="{tab_id}-tab" data-bs-toggle="tab" data-bs-target="#{tab_id}" type="button" role="tab">{league_name}</button></li>')

        # 生成表格行
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
                        <tr>
                            <th>排名</th><th>球队</th><th>场次</th><th>胜</th><th>平</th><th>负</th>
                            <th>进球</th><th>失球</th><th>净胜球</th><th>积分</th>
                        </tr>
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
        .header h1 {{ color: #1e3c72; font-weight: 700; letter-spacing: 1px; }}
        .header p {{ color: #2c5282; }}
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

    <footer>
        © 烽域·星舟 | 数据来源：football.json 开源项目
    </footer>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 报告已生成: {OUTPUT_FILE}")

# ==================== Git 自动提交推送 ====================
def git_auto_push():
    """在仓库根目录执行 add, commit, push"""
    try:
        # 添加所有变更
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        # 检查是否有变更可提交
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("📭 没有需要提交的变更，跳过提交。")
            return

        # 生成提交信息
        commit_msg = f"Auto-update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True, text=True)
        print(f"📦 已提交: {commit_msg}")

        # 推送
        subprocess.run(["git", "push"], check=True, capture_output=True, text=True)
        print("🚀 已推送到远程仓库")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失败: {e}")
        if e.stderr:
            print(e.stderr)
        # 不退出，让主流程继续

# ==================== 主程序 ====================
def main():
    print("⚽ 烽域·星舟 积分榜生成器启动")
    tables = {}

    for display_name, folder in LEAGUES.items():
        print(f"加载 {display_name}...")
        matches, _ = load_league_data(display_name, folder)
        if matches:
            table = calculate_table(matches)
            tables[display_name] = table
        else:
            print(f"  ⚠️ {display_name} 无有效数据")
            tables[display_name] = []

    if not tables:
        print("❌ 没有加载到任何联赛数据，请检查 football.json 文件夹路径")
        return

    generate_html(tables)
    git_auto_push()

if __name__ == "__main__":
    main()