import json
import re
import sys
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class AIGameEngine:
    """AI对战游戏引擎 - 增强版（修复敌人反击问题）"""
    
    def __init__(self, api_key: Optional[str] = None, use_mock: bool = False):
        """
        初始化游戏引擎
        
        Args:
            api_key: OpenAI API密钥，如果为None则使用模拟模式
            use_mock: 强制使用模拟模式，即使提供了API密钥
        """
        self.use_mock = use_mock or (api_key is None)
        self.api_key = api_key
        self.ai_enabled = False
        self.client = None
        
        if not self.use_mock:
            try:
                # 尝试导入openai库
                from openai import OpenAI
                
                # 验证API密钥格式
                if not api_key or not isinstance(api_key, str) or len(api_key.strip()) < 10:
                    print("警告: API密钥格式不正确，切换到模拟模式")
                    self.use_mock = True
                else:
                    try:
                        # 创建客户端并测试连接
                        self.client = OpenAI(
                            api_key=api_key,
                            base_url="https://api.deepseek.com",
                            timeout=30.0  # 增加超时时间
                        )
                        
                        # 快速测试连接
                        test_response = self.client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": "测试连接"}],
                            max_tokens=10
                        )
                        
                        if test_response.choices[0].message.content:
                            self.ai_enabled = True
                            self.model = "deepseek-chat"
                            print("✅ API连接成功，使用真实AI模式")
                        else:
                            print("警告: API测试失败，切换到模拟模式")
                            self.use_mock = True
                            
                    except Exception as e:
                        print(f"警告: API连接失败 ({type(e).__name__})，切换到模拟模式")
                        print(f"错误详情: {str(e)}")
                        self.use_mock = True
                        
            except ImportError:
                print("警告: 未安装openai库，请运行: pip install openai")
                print("切换到模拟模式")
                self.use_mock = True
                self.ai_enabled = False
            except Exception as e:
                print(f"警告: 初始化失败 ({type(e).__name__})，切换到模拟模式")
                print(f"错误详情: {str(e)}")
                self.use_mock = True
        else:
            self.ai_enabled = False
            print("使用模拟模式运行")
        
        # 游戏状态
        self.game_data = {
            "player": {"name": "", "hp": 0, "max_hp": 0, "conc": 0, "skills": []},
            "enemy": {"name": "", "hp": 0, "max_hp": 0, "conc": 0, "skills": []},
            "battle_reason": "",
            "history": [],
            "current_summary": "战斗开始...",
            "round": 0,
            "phase": "init",
            "mode": "模拟" if self.use_mock else "真实AI",
            "enemy_skills_used": []  # 记录敌人使用过的技能
        }
    
    def _call_ai_mock(self, prompt: str, temperature: float = 0.7) -> str:
        """模拟AI响应（增强版，包含敌人反击）"""
        # 根据prompt内容返回不同的模拟响应
        if "初始化" in prompt or "初始设定" in prompt:
            return json.dumps({
                "player": {"name": "流浪武士", "hp": 1200, "max_hp": 1200, "conc": 100, 
                          "atk": 3, "spd": 7, "skills": [
                              {"name": "拔刀斩", "cost": 20, "effect": "造成200-300伤害"},
                              {"name": "心眼", "cost": 15, "effect": "下回合攻击必中"},
                              {"name": "剑气护体", "cost": 25, "effect": "获得200点护盾"},
                              {"name": "冥想", "cost": 0, "effect": "恢复50点CONC"}
                          ]},
                "enemy": {"name": "机械章鱼", "hp": 1500, "max_hp": 1500, "conc": 100,
                         "atk": 4, "spd": 5, "skills": [
                             {"name": "触手鞭笞", "cost": 20, "effect": "造成180-280伤害"},
                             {"name": "油污喷射", "cost": 25, "effect": "降低目标SPD 3点"},
                             {"name": "电磁脉冲", "cost": 30, "effect": "沉默目标1回合"},
                             {"name": "能量回收", "cost": 0, "effect": "恢复40点CONC"}
                         ]},
                "reason": "争夺最后的反物质电池，为各自的族群续命",
                "opening": "硝烟弥漫的废土上，武士的刀锋与机械的触手遥相对峙..."
            }, ensure_ascii=False, indent=2)
        
        # 战斗回合的模拟响应（增强敌人反击）
        current_round = self.game_data["round"] + 1
        
        # 模拟不同的战斗情况，包含敌人反击
        if current_round <= 3:
            # 前3回合：激烈交锋，敌人会反击
            narrative = f"第{current_round}回合：{self.game_data['player']['name']}发起攻击，{self.game_data['enemy']['name']}迅速反击！"
            enemy_skill = "触手鞭笞"
            dialogue = f"{self.game_data['enemy']['name']}：尝尝这个！{enemy_skill}！"
            player_damage = 120
            enemy_damage = 100
        elif current_round <= 6:
            # 4-6回合：战斗白热化
            narrative = f"第{current_round}回合：战斗进入白热化！双方都使出强力技能！"
            enemy_skill = "油污喷射"
            dialogue = f"{self.game_data['enemy']['name']}：检测到威胁升级，启动{enemy_skill}！"
            player_damage = 180
            enemy_damage = 150
        elif current_round <= 9:
            # 7-9回合：决胜阶段
            narrative = f"第{current_round}回合：决胜时刻！双方都拿出了压箱底的绝招！"
            enemy_skill = "电磁脉冲"
            dialogue = f"{self.game_data['enemy']['name']}：释放{enemy_skill}，你无法行动了！"
            player_damage = 250
            enemy_damage = 200
        else:
            # 10+回合：战斗尾声
            narrative = f"第{current_round}回合：战斗接近尾声，双方都已精疲力竭..."
            enemy_skill = "触手鞭笞"
            dialogue = "双方都喘息着，寻找最后一击的机会..."
            player_damage = 100
            enemy_damage = 80
        
        # 记录敌人使用的技能
        if enemy_skill not in self.game_data["enemy_skills_used"]:
            self.game_data["enemy_skills_used"].append(enemy_skill)
        
        # 计算新的HP值（确保不会低于0）
        player_hp = max(0, self.game_data["player"]["hp"] - enemy_damage)
        enemy_hp = max(0, self.game_data["enemy"]["hp"] - player_damage)
        
        # 计算CONC值
        player_conc = max(0, self.game_data["player"]["conc"] - 20)
        enemy_conc = max(0, self.game_data["enemy"]["conc"] - 25)
        
        # 根据HP判断阶段
        if player_hp <= 300 or enemy_hp <= 300:
            phase = "climax"
        elif player_hp <= 0 or enemy_hp <= 0:
            phase = "ending"
        else:
            phase = "battle"
        
        return json.dumps({
            "narrative": narrative,
            "status": {
                "player_hp": player_hp,
                "enemy_hp": enemy_hp,
                "player_conc": player_conc,
                "enemy_conc": enemy_conc
            },
            "phase": phase,
            "dialogue": dialogue,
            "damage_dealt": f"玩家造成了{player_damage}点伤害，敌人造成了{enemy_damage}点伤害",
            "enemy_skill_used": enemy_skill,
            "player_skill_used": "模拟技能"
        }, ensure_ascii=False, indent=2)
    
    def _call_ai_real(self, prompt: str, temperature: float = 0.7, max_retries: int = 3) -> str:
        """调用真实的AI API，带重试机制"""
        if not self.client or not self.ai_enabled:
            print("警告: AI客户端未初始化，使用模拟模式")
            return self._call_ai_mock(prompt, temperature)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=1500,
                    timeout=30.0
                )
                return response.choices[0].message.content
                
            except Exception as e:
                error_type = type(e).__name__
                print(f"⚠️  AI调用失败 (尝试 {attempt + 1}/{max_retries}): {error_type}")
                
                if attempt < max_retries - 1:
                    # 不是最后一次重试，等待后重试
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    # 最后一次重试也失败
                    print(f"❌❌ 所有重试失败，切换到模拟模式: {str(e)}")
                    return self._call_ai_mock(prompt, temperature)
        
        # 所有重试都失败（理论上不会执行到这里）
        return self._call_ai_mock(prompt, temperature)
    
    def call_ai(self, prompt: str, temperature: float = 0.7) -> str:
        """统一的AI调用接口"""
        if self.use_mock or not self.ai_enabled:
            return self._call_ai_mock(prompt, temperature)
        else:
            return self._call_ai_real(prompt, temperature)
    
    def extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON，带错误处理"""
        # 清理文本中的多余空白和换行
        text = text.strip()
        
        try:
            # 尝试直接解析
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始文本前200字符: {text[:200]}")
            
            # 尝试提取JSON部分
            try:
                # 查找第一个{和最后一个}
                start = text.find('{')
                end = text.rfind('}') + 1
                
                if start != -1 and end != 0:
                    json_str = text[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            # 尝试修复常见的JSON格式问题
            try:
                # 移除注释
                lines = text.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if not line.startswith('//') and not line.startswith('#'):
                        cleaned_lines.append(line)
                cleaned_text = '\n'.join(cleaned_lines)
                
                # 尝试再次解析
                return json.loads(cleaned_text)
            except:
                pass
        
        # 如果都失败，返回一个安全的默认值
        print("⚠️  JSON解析完全失败，使用模拟数据")
        return json.loads(self._call_ai_mock("模拟数据", temperature=0.7))
    
    def initialize_game(self, player_name: str, enemy_name: str) -> Dict[str, Any]:
        """初始化游戏"""
        prompt = f"""
请为{player_name}和{enemy_name}创建战斗初始设定，包括：
1. 双方属性（HP 800-2000, CONC 100, ATK 1-5星, SPD 1-10）
2. 各4个技能（必须包含1个恢复CONC技能）
3. 有创意的开战原因
4. 简短的开场剧情

请严格使用以下JSON格式，不要添加任何额外文本，不要使用markdown：
{{
    "player": {{
        "name": "角色名称",
        "hp": 数值,
        "max_hp": 数值,
        "conc": 数值,
        "atk": 数值,
        "spd": 数值,
        "skills": [
            {{"name": "技能1", "cost": 消耗值, "effect": "效果描述"}},
            {{"name": "技能2", "cost": 消耗值, "effect": "效果描述"}},
            {{"name": "技能3", "cost": 消耗值, "effect": "效果描述"}},
            {{"name": "技能4", "cost": 消耗值, "effect": "效果描述"}}
        ]
    }},
    "enemy": {{
        "name": "角色名称",
        "hp": 数值,
        "max_hp": 数值,
        "conc": 数值,
        "atk": 数值,
        "spd": 数值,
        "skills": [
            {{"name": "技能1", "cost": 消耗值, "effect": "效果描述"}},
            {{"name": "技能2", "cost": 消耗值, "effect": "效果描述"}},
            {{"name": "技能3", "cost": 消耗值, "effect": "效果描述"}},
            {{"name": "技能4", "cost": 消耗值, "effect": "效果描述"}}
        ]
    }},
    "reason": "开战原因描述",
    "opening": "开场剧情描述"
}}
        """
        
        print(f"正在初始化游戏: {player_name} vs {enemy_name}...")
        response = self.call_ai(prompt, temperature=0.8)
        print(f"AI响应长度: {len(response)} 字符")
        
        data = self.extract_json(response)
        
        # 更新游戏数据
        if "player" in data and "enemy" in data:
            self.game_data.update({
                "player": data["player"],
                "enemy": data["enemy"],
                "battle_reason": data.get("reason", "未知原因"),
                "phase": "battle",
                "round": 0,
                "enemy_skills_used": []
            })
            
            # 确保有默认值
            if "hp" not in self.game_data["player"]:
                self.game_data["player"]["hp"] = 1000
                self.game_data["player"]["max_hp"] = 1000
                self.game_data["player"]["conc"] = 100
                
            if "hp" not in self.game_data["enemy"]:
                self.game_data["enemy"]["hp"] = 1200
                self.game_data["enemy"]["max_hp"] = 1200
                self.game_data["enemy"]["conc"] = 100
            
            # 添加初始记录
            self.game_data["history"].append({
                "type": "init",
                "data": data,
                "narrative": data.get("opening", "战斗开始！"),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            print("✅ 游戏初始化成功")
        else:
            print("⚠️  游戏初始化数据不完整，使用默认数据")
            # 使用默认数据
            default_data = json.loads(self._call_ai_mock("初始化", 0.7))
            self.game_data.update({
                "player": default_data["player"],
                "enemy": default_data["enemy"],
                "battle_reason": default_data.get("reason", "未知原因"),
                "phase": "battle",
                "round": 0,
                "enemy_skills_used": []
            })
            
            self.game_data["history"].append({
                "type": "init",
                "data": default_data,
                "narrative": default_data.get("opening", "战斗开始！"),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            data = default_data
        
        return data
    
    def update_summary(self):
        """更新战斗摘要"""
        if len(self.game_data["history"]) < 2:
            return
        
        # 每3回合或当有重大事件时更新摘要
        if len(self.game_data["history"]) % 3 == 0:
            recent_history = self.game_data["history"][-3:]
            summary_prompt = f"请用100字以内总结以下战斗历史：{recent_history}"
            try:
                summary = self.call_ai(summary_prompt, temperature=0.3)
                if summary and len(summary) > 10:
                    self.game_data["current_summary"] = summary
                    print(f"📝📝 已更新战斗摘要")
            except Exception as e:
                print(f"摘要更新失败: {e}")
    
    def play_round(self, player_action: str) -> Dict[str, Any]:
        """执行一个战斗回合（修复版：包含敌人反击）"""
        self.game_data["round"] += 1
        
        # 获取敌人技能信息
        enemy_skills = self.game_data["enemy"].get("skills", [])
        enemy_skills_desc = "\n".join([f"  - {skill.get('name', '未知技能')}: {skill.get('effect', '效果未知')}" for skill in enemy_skills])
        
        # 构建上下文
        context = {
            "summary": self.game_data["current_summary"],
            "player_hp": self.game_data["player"]["hp"],
            "enemy_hp": self.game_data["enemy"]["hp"],
            "round": self.game_data["round"],
            "phase": self.game_data["phase"],
            "player_name": self.game_data["player"]["name"],
            "enemy_name": self.game_data["enemy"]["name"]
        }
        
        prompt = f"""
基于以下战斗上下文生成本回合内容：
战斗摘要：{context['summary']}
当前回合：第{context['round']}回合
当前阶段：{context['phase']}
玩家角色：{context['player_name']} (HP: {context['player_hp']})
敌人角色：{context['enemy_name']} (HP: {context['enemy_hp']})
玩家行动：{player_action}

敌人可用技能：
{enemy_skills_desc}

重要要求：
1. 必须包含敌人的反击行动或技能使用，不能只有单方面攻击
2. 战斗叙述要体现双方互动，描述敌人的应对策略
3. 根据双方行动合理计算伤害和状态变化
4. 敌人会根据当前战况智能选择技能进行反击

请生成包含以下内容的JSON，不要添加任何额外文本，不要使用markdown：
{{
    "narrative": "生动的战斗叙述（必须包含玩家的行动和敌人的反击行动）",
    "status": {{
        "player_hp": 战斗后玩家HP（0-2000之间的整数）,
        "enemy_hp": 战斗后敌人HP（0-2000之间的整数）,
        "player_conc": 战斗后玩家CONC（0-100之间的整数）,
        "enemy_conc": 战斗后敌人CONC（0-100之间的整数）
    }},
    "phase": "battle/climax/ending",
    "dialogue": "本回合的关键对话",
    "damage_dealt": "双方造成的伤害描述",
    "player_skill_used": "玩家使用的技能名称",
    "enemy_skill_used": "敌人使用的技能名称"
}}
        """
        
        print(f"🔄🔄 正在生成第{context['round']}回合战斗...")
        response = self.call_ai(prompt)
        round_data = self.extract_json(response)
        
        # 验证并修正状态数据
        if "status" in round_data:
            status = round_data["status"]
            
            # 确保HP在合理范围内
            status["player_hp"] = max(0, min(status.get("player_hp", 0), 2000))
            status["enemy_hp"] = max(0, min(status.get("enemy_hp", 0), 2000))
            
            # 确保CONC在合理范围内
            status["player_conc"] = max(0, min(status.get("player_conc", 0), 100))
            status["enemy_conc"] = max(0, min(status.get("enemy_conc", 0), 100))
            
            # 更新游戏状态
            self.game_data["player"]["hp"] = status["player_hp"]
            self.game_data["enemy"]["hp"] = status["enemy_hp"]
            self.game_data["player"]["conc"] = status["player_conc"]
            self.game_data["enemy"]["conc"] = status["enemy_conc"]
        
        if "phase" in round_data:
            self.game_data["phase"] = round_data["phase"]
        
        # 记录敌人使用的技能
        enemy_skill_used = round_data.get("enemy_skill_used", "")
        if enemy_skill_used and enemy_skill_used not in self.game_data["enemy_skills_used"]:
            self.game_data["enemy_skills_used"].append(enemy_skill_used)
        
        # 记录历史
        self.game_data["history"].append({
            "round": self.game_data["round"],
            "action": player_action,
            "player_skill": round_data.get("player_skill_used", ""),
            "enemy_skill": enemy_skill_used,
            "data": round_data,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # 更新摘要
        self.update_summary()
        
        return round_data
    
    def is_game_over(self) -> bool:
        """检查游戏是否结束"""
        return (
            self.game_data["player"]["hp"] <= 0 or
            self.game_data["enemy"]["hp"] <= 0 or
            self.game_data["phase"] == "ending" or
            self.game_data["round"] >= 20
        )
    
    def get_game_status(self) -> Dict[str, Any]:
        """获取当前游戏状态"""
        return {
            "round": self.game_data["round"],
            "phase": self.game_data["phase"],
            "player": self.game_data["player"].copy(),
            "enemy": self.game_data["enemy"].copy(),
            "game_over": self.is_game_over(),
            "history_count": len(self.game_data["history"]),
            "mode": self.game_data["mode"],
            "enemy_skills_used": self.game_data["enemy_skills_used"].copy()
        }
    
    def get_skill_menu(self) -> str:
        """获取技能菜单"""
        menu = "🎯🎯 可选技能：\n"
        skills = self.game_data["player"].get("skills", [])
        
        if not skills:
            menu = "暂无技能信息\n"
        else:
            for i, skill in enumerate(skills, 1):
                name = skill.get('name', '未知技能')
                effect = skill.get('effect', '效果未知')
                cost = skill.get('cost', 0)
                menu += f"  {i}. {name} - {effect} (消耗: {cost} CONC)\n"
        
        return menu
    
    def get_enemy_skills(self) -> str:
        """获取敌人技能信息"""
        menu = "👹👹 敌人技能：\n"
        skills = self.game_data["enemy"].get("skills", [])
        
        if not skills:
            menu = "暂无敌人技能信息\n"
        else:
            for i, skill in enumerate(skills, 1):
                name = skill.get('name', '未知技能')
                effect = skill.get('effect', '效果未知')
                cost = skill.get('cost', 0)
                menu += f"  {i}. {name} - {effect} (消耗: {cost} CONC)\n"
        
        return menu
    
    def get_enemy_skills_used(self) -> str:
        """获取敌人已使用的技能"""
        if not self.game_data["enemy_skills_used"]:
            return "👹 敌人尚未使用任何技能"
        
        menu = "👹👹 敌人已使用技能：\n"
        for i, skill in enumerate(self.game_data["enemy_skills_used"], 1):
            menu += f"  {i}. {skill}\n"
        
        return menu

def test_api_connection(api_key: str) -> bool:
    """测试API连接"""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=10.0
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "测试连接，请回复'连接成功'"}],
            max_tokens=10
        )
        
        if "连接成功" in response.choices[0].message.content:
            print("✅ API连接测试成功")
            return True
        else:
            print("⚠️  API响应异常")
            return False
            
    except Exception as e:
        print(f"❌❌ API连接测试失败: {type(e).__name__}: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🤖🤖 AI对战游戏 - 增强修复版")
    print("=" * 60)
    
    # 显示运行模式
    print("\n🏃🏃 运行模式选择：")
    print("  1. 模拟模式 (无需API密钥，使用预设数据)")
    print("  2. API模式 (需要DeepSeek API密钥)")
    print("  3. 测试API连接")
    
    choice = input("\n请输入选择 (1/2/3): ").strip()
    
    game = None
    
    if choice == "3":
        # 测试API连接
        api_key = input("请输入DeepSeek API密钥: ").strip()
        if test_api_connection(api_key):
            print("\n✅ API连接正常，您可以开始游戏了！")
            choice = "2"  # 自动切换到API模式
        else:
            print("\n❌❌ API连接失败，请检查密钥和网络连接")
            print("将使用模拟模式运行游戏")
            choice = "1"
    
    if choice == "2":
        api_key = input("请输入DeepSeek API密钥: ").strip()
        if not api_key:
            print("未提供API密钥，切换到模拟模式")
            game = AIGameEngine(use_mock=True)
        else:
            game = AIGameEngine(api_key=api_key, use_mock=False)
    else:
        game = AIGameEngine(use_mock=True)
    
    print("\n" + "=" * 60)
    
    # 获取角色名称
    player_name = input("请输入你的角色名称 (默认: 流浪武士): ").strip() or "流浪武士"
    enemy_name = input("请输入敌方角色名称 (默认: 机械章鱼): ").strip() or "机械章鱼"
    
    print(f"\n正在初始化游戏: {player_name} 🆚🆚🆚 {enemy_name}")
    print("⏳⏳⏳ 请稍候..." if game.game_data["mode"] == "真实AI" else "")
    
    # 初始化游戏
    try:
        init_data = game.initialize_game(player_name, enemy_name)
        
        if "error" in init_data:
            print(f"❌❌ 初始化失败: {init_data['error']}")
            return
        
        print("\n" + "=" * 60)
        print(f"🎮🎮 游戏模式: {game.game_data['mode']}模式")
        print(f"🎯🎯 开战原因: {game.game_data['battle_reason']}")
        print(f"📖📖 开场剧情: {game.game_data['history'][0]['narrative']}")
        print(f"❤️  玩家: {game.game_data['player']['name']} (HP: {game.game_data['player']['hp']}/{game.game_data['player']['max_hp']})")
        print(f"⚔⚔️  敌方: {game.game_data['enemy']['name']} (HP: {game.game_data['enemy']['hp']}/{game.game_data['enemy']['max_hp']})")
        
        # 显示玩家技能
        print("\n" + game.get_skill_menu())
        # 显示敌人技能
        print(game.get_enemy_skills())
        
    except Exception as e:
        print(f"❌❌ 游戏初始化异常: {e}")
        print("使用默认配置继续游戏...")
        # 使用模拟数据继续
        game.game_data["player"] = {"name": player_name, "hp": 1200, "max_hp": 1200, "conc": 100, "skills": []}
        game.game_data["enemy"] = {"name": enemy_name, "hp": 1500, "max_hp": 1500, "conc": 100, "skills": []}
        game.game_data["battle_reason"] = "未知原因的对决"
    
    print("\n" + "=" * 60)
    print("🎮🎮 游戏开始！")
    print("📝📝 输入技能编号或描述你的行动")
    print("ℹℹ️  命令: 'quit'-退出, 'status'-状态, 'skills'-技能, 'enemy_skills'-敌人技能, 'enemy_used'-敌人已用技能, 'help'-帮助")
    print("=" * 60)
    
    # 游戏主循环
    while not game.is_game_over():
        print(f"\n--- 第 {game.game_data['round'] + 1} 回合 ---")
        
        # 获取玩家输入
        try:
            action = input("> 你的行动: ").strip()
            
            if not action:
                print("⚠️  请输入有效行动")
                continue
            
            action_lower = action.lower()
            
            if action_lower in ['quit', 'exit', 'q']:
                print("游戏结束")
                break
            elif action_lower in ['status', 'stats', 's']:
                status = game.get_game_status()
                print(f"\n📊📊 当前状态:")
                print(f"   回合: {status['round']}")
                print(f"   阶段: {status['phase']}")
                print(f"   模式: {status['mode']}模式")
                print(f"   玩家: {status['player']['name']} (HP: {status['player']['hp']}/{status['player']['max_hp']}, CONC: {status['player']['conc']})")
                print(f"   敌人: {status['enemy']['name']} (HP: {status['enemy']['hp']}/{status['enemy']['max_hp']}, CONC: {status['enemy']['conc']})")
                continue
            elif action_lower in ['skills', 'skill', 'sk']:
                print("\n" + game.get_skill_menu())
                continue
            elif action_lower in ['enemy_skills', 'enemy', 'es']:
                print("\n" + game.get_enemy_skills())
                continue
            elif action_lower in ['enemy_used', 'eu']:
                print("\n" + game.get_enemy_skills_used())
                continue
            elif action_lower in ['help', 'h']:
                print("\n📚📚 帮助信息:")
                print("   1. 输入技能编号 (如: 1) 使用对应技能")
                print("   2. 输入行动描述 (如: 使用火焰攻击)")
                print("   3. 命令:")
                print("      - quit/exit/q: 退出游戏")
                print("      - status/stats/s: 查看状态")
                print("      - skills/skill/sk: 查看玩家技能")
                print("      - enemy_skills/enemy/es: 查看敌人技能")
                print("      - enemy_used/eu: 查看敌人已用技能")
                print("      - help/h: 查看帮助")
                continue
            
            # 处理技能编号
            if action.isdigit():
                skill_num = int(action)
                skills = game.game_data["player"].get("skills", [])
                if 1 <= skill_num <= len(skills):
                    skill = skills[skill_num - 1]
                    action = f"使用技能[{skill['name']}]: {skill['effect']}"
                else:
                    print(f"⚠️  无效的技能编号，请输入1-{len(skills)}之间的数字")
                    continue
            
            # 执行回合
            print(f"⚡⚡ 执行: {action}")
            print("🔄🔄 AI正在生成战斗过程..." if game.game_data["mode"] == "真实AI" else "🔄🔄 生成战斗过程...")
            
            result = game.play_round(action)
            
            # 显示结果
            if "error" in result:
                print(f"❌❌ 错误: {result['error']}")
            else:
                print(f"\n📖📖 {result.get('narrative', '战斗继续...')}")
                if result.get('dialogue'):
                    print(f"💬💬 {result['dialogue']}")
                
                status = result.get("status", {})
                print(f"\n❤️  状态更新:")
                print(f"   玩家 HP: {status.get('player_hp', '?')}/{game.game_data['player']['max_hp']}")
                print(f"   敌人 HP: {status.get('enemy_hp', '?')}/{game.game_data['enemy']['max_hp']}")
                print(f"   玩家 CONC: {status.get('player_conc', '?')}/100")
                print(f"   敌人 CONC: {status.get('enemy_conc', '?')}/100")
                
                # 显示使用的技能
                if result.get('player_skill_used'):
                    print(f"🎯🎯 玩家使用了: {result['player_skill_used']}")
                if result.get('enemy_skill_used'):
                    print(f"👹👹 敌人使用了: {result['enemy_skill_used']}")
                
                if result.get('damage_dealt'):
                    print(f"⚡⚡ {result['damage_dealt']}")
                
                # 检查游戏结束条件
                if game.is_game_over():
                    break
                    
        except KeyboardInterrupt:
            print("\n\n⏹⏹⏹️  游戏中断")
            break
        except Exception as e:
            print(f"❌❌ 回合执行异常: {e}")
            # 继续游戏
            continue
    
    # 游戏结束
    print("\n" + "=" * 60)
    print("🎮🎮 游戏结束！")
    
    final_status = game.get_game_status()
    print(f"📊📊 最终统计:")
    print(f"   总回合数: {final_status['round']}")
    print(f"   最终阶段: {final_status['phase']}")
    print(f"   运行模式: {final_status['mode']}模式")
    
    # 显示敌人使用过的所有技能
    if final_status['enemy_skills_used']:
        print(f"👹👹 敌人使用过的技能:")
        for i, skill in enumerate(final_status['enemy_skills_used'], 1):
            print(f"     {i}. {skill}")
    
    if final_status['player']['hp'] <= 0 and final_status['enemy']['hp'] <= 0:
        print("🏁🏁 结果: 平局！双方同归于尽")
    elif final_status['player']['hp'] <= 0:
        print(f"💀💀 结果: {final_status['player']['name']}被击败了！")
    elif final_status['enemy']['hp'] <= 0:
        print(f"🎉🎉 结果: {final_status['player']['name']}获胜了！")
    else:
        print("🏁🏁 结果: 战斗未分胜负")
    
    print(f"\n📝📝 战斗摘要: {game.game_data['current_summary']}")
    print("=" * 60)
    print("感谢游玩！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌❌ 程序运行异常: {e}")
        print("请检查输入和网络连接，或使用模拟模式运行。")
        print("按Enter键退出...")
        input()
