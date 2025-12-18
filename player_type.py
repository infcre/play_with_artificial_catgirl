'''
@Description：第五人格角色模拟系统
'''

class Survivor:
    """求生者类"""

    """
    构造方法：用于在创建对象时初始化对象的状态
    __init__ 方法不是必需的。如果你不定义它，Python 会提供一个默认的无参构造方法。
    如果你定义了带参数的 __init__ 方法，在创建类的实例时必须提供相应的参数。
    __init__ 方法不应该返回任何值（即不要使用 return 语句返回一个值），否则会导致错误。
    """

    def __init__(self, name):
        """初始化求生者属性"""
        self.name = name  # 角色名称
        self.health = 100  # 生命值（0-100）
        self.is_alive = True  # 存活状态

    """
    用于定义对象的非正式字符串表示形式,适合用于打印输出或者调试信息。
    当使用 print() 函数或者 str() 函数作用于对象时，会自动调用该对象的 __str__ 方法。
    """

    def __str__(self):
        """返回角色描述信息"""
        return f'求生者：{self.name},生命值：{self.health}'

    def take_damage(self, damage):
        """承受伤害处理（核心逻辑）"""
        if not self.is_alive:  # 如果角色已经死亡
            print(f"{self.name}已经死亡，无法再受到伤害。")
            return False  # 返回操作失败

        elif damage >= self.health:  # 如果伤害值大于等于当前生命值
            self.health = 0  # 生命值归零
            self.is_alive = False  # 更新存活状态为死亡
            print(f"{self.name}受到了致命一击,伤害值{damage},生命值归零!{self.name}已经死亡")
            return False  # 返回操作失败

        else:
            self.health -= damage  # 减少生命值
            print(f"{self.name}受到了{damage}点伤害，剩余生命值：{self.health}")
            return True  # 返回操作成功

    def escape(self):
        """逃脱行为处理"""
        if self.is_alive:  # 如果角色存活
            print(f"{self.name}逃脱了监管者的追捕")
            return True  # 逃脱成功
        else:
            print(f"求生者{self.name}已死亡，无法逃脱")
            return False  # 逃脱失败

    def heal(self, amount):
        """治疗行为处理"""
        if not self.is_alive:  # 如果角色已经死亡
            print(f"{self.name}已经死亡,无法恢复生命值")
            return False  # 返回操作失败
        if self.health == 100:  # 如果生命值已经满了
            print(f"{self.name}的生命值已经是满的,无需再回复")
            return False  # 返回操作失败

        # 计算实际治疗量（防止溢出，确保治疗后的生命值不会超过100）
        healed_amount = min(100 - self.health, amount)  # 取治疗量与剩余生命差值的最小值
        self.health += healed_amount  # 恢复生命值
        print(f"{self.name}恢复了{healed_amount}点生命值,当前生命值:{self.health}")
        return True  # 返回操作成功


class Hunter:
    """监管者类"""

    def __init__(self, name):
        """初始化监管者属性"""
        self.name = name  # 角色名称
        self.attack_damage = 30  # 初始攻击伤害值

    def __str__(self):
        """返回角色描述信息"""
        return f"监管者：{self.name},攻击伤害值为：{self.attack_damage}"

    def attack(self, survivor):
        """攻击求生者"""
        print(f"{self.name}对{survivor.name}发起攻击！")
        survivor.take_damage(self.attack_damage)  # 进行攻击，扣除求生者生命值

    def add_damage(self, amount):
        """增强攻击力"""
        self.attack_damage += amount  # 增加攻击伤害
        print(f"{self.name}的攻击伤害值增加了{amount}点，当前攻击伤害值：{self.attack_damage}")


if __name__ == "__main__":
    """测试用例1：基础功能验证"""
    print("\n=== 测试用例1 ===")
    survivor = Survivor("医生")  # 创建一个求生者角色
    print(survivor)  # 测试__str__方法，输出求生者信息

    # 连续伤害测试
    survivor.take_damage(30)  # 求生者受到了30点伤害
    survivor.take_damage(30)  # 求生者再受到了30点伤害
    survivor.take_damage(30)  # 求生者再受到了30点伤害

    survivor.escape()  # 测试求生者逃脱功能

    # 治疗测试
    survivor.heal(120)  # 尝试治疗，但实际只能恢复生命值至100
    survivor.take_damage(100)  # 求生者受到致命伤害
    survivor.heal(120)  # 死亡后尝试治疗，应该无法治疗

    """测试用例2：角色交互测试"""
    print("\n=== 测试用例2 ===")
    survivor = Survivor("医生")  # 创建一个求生者角色
    hunter = Hunter("小丑")  # 创建一个监管者角色

    # 初始攻击
    hunter.attack(survivor)  # 监管者攻击求生者

    # 强化后攻击
    hunter.add_damage(10)  # 监管者提升攻击力
    hunter.attack(survivor)  # 进行攻击
    hunter.attack(survivor)  # 再次攻击求生者，造成致命伤害，求生者死亡