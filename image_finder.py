import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
import os
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import pyperclip

def locate_image_on_screen(template_path, threshold=0.8):
    """
    在屏幕上查找模板图像的位置

    参数:
        template_path: 模板图像的路径
        threshold: 匹配阈值，范围0-1，值越高匹配越严格

    返回:
        中心点坐标(x, y)，如果未找到则返回None
    """
    # 加载模板图像
    if not os.path.exists(template_path):
        print(f"错误：模板图像 '{template_path}' 不存在")
        return None

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        print(f"错误：无法加载模板图像 '{template_path}'")
        return None

    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    template_height, template_width = template_gray.shape[:2]

    # 截取当前屏幕
    print("正在截取屏幕...")
    screenshot = np.array(ImageGrab.grab())
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    # 使用模板匹配
    print("正在进行图像匹配...")
    result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 判断匹配结果
    if max_val >= threshold:
        top_left = max_loc
        center_x = top_left[0] + template_width // 2
        center_y = top_left[1] + template_height // 2
        print(f"找到匹配图像！置信度: {max_val:.2f}, 坐标: ({center_x}, {center_y})")

        # 在截图上标记匹配位置
        marked_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        cv2.rectangle(marked_screenshot, top_left, bottom_right, (0, 255, 0), 2)
        marked_screenshot_path = f"matched_result_{os.path.basename(template_path)}"
        cv2.imwrite(marked_screenshot_path, marked_screenshot)
        print(f"匹配结果已保存至: {marked_screenshot_path}")

        return (center_x, center_y)
    else:
        print(f"未找到匹配图像，最高置信度: {max_val:.2f}，低于阈值 {threshold}")
        return None

def move_mouse_to_coordinate(x, y, duration=0.5):
    """
    移动鼠标到指定坐标

    参数:
        x, y: 目标坐标
        duration: 移动持续时间（秒）
    """
    print(f"准备将鼠标移动到坐标: ({x}, {y})")
    # 检查坐标是否在屏幕范围内
    screen_width, screen_height = pyautogui.size()
    if 0 <= x < screen_width and 0 <= y < screen_height:
        pyautogui.moveTo(x, y, duration=duration)
        print(f"鼠标已移动到坐标: ({x}, {y})")
    else:
        print(f"错误：坐标 ({x}, {y}) 超出屏幕范围 ({screen_width}, {screen_height})")

def click_mouse(x=None, y=None, button='left', clicks=1, interval=0.1):
    """
    点击鼠标

    参数:
        x, y: 点击位置坐标，若为None则使用当前鼠标位置
        button: 鼠标按键，'left', 'right' 或 'middle'
        clicks: 点击次数
        interval: 多次点击之间的间隔时间（秒）
    """
    if x is not None and y is not None:
        pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
        print(f"在坐标 ({x}, {y}) 处执行 {clicks} 次{button}键点击")
    else:
        pyautogui.click(clicks=clicks, interval=interval, button=button)
        print(f"在当前位置执行 {clicks} 次{button}键点击")

def type_text(text, interval=0.1, use_clipboard=True):
    """
    输入文本

    参数:
        text: 要输入的文本
        interval: 字符之间的输入间隔（秒）
        use_clipboard: 是否使用剪贴板输入（处理中文）
    """
    if use_clipboard:
        # 保存当前剪贴板内容
        old_clipboard = pyperclip.paste()

        # 将文本复制到剪贴板
        pyperclip.copy(text)

        # 模拟粘贴操作
        pyautogui.hotkey('ctrl', 'v')

        # 恢复剪贴板内容
        pyperclip.copy(old_clipboard)

        print(f"通过剪贴板输入文本: '{text}'")
    else:
        # 直接输入（仅适用于英文和可直接输入的字符）
        print(f"直接输入文本: '{text}'")
        pyautogui.typewrite(text, interval=interval)

def press_key(key):
    """
    按下单个按键

    参数:
        key: 按键名称，如 'enter', 'tab', 'esc' 等
    """
    print(f"按下按键: {key}")
    pyautogui.press(key)

def execute_action(action, root=None, config_food=None):
    """
    执行单个操作步骤

    参数:
        action: 操作配置字典
        root: Tkinter根窗口，用于显示对话框
    """
    action_type = action.get("type")

    if action_type == "find_image":
        # 查找图像
        template_path = action.get("template_path")
        threshold = action.get("threshold", 0.8)

        if not template_path:
            print("错误：缺少template_path参数")
            return None

        print(f"步骤: 查找图像 - {template_path}")
        coordinates = locate_image_on_screen(template_path, threshold)

        if coordinates:
            # 保存坐标供后续操作使用
            return coordinates
        else:
            # 处理图像未找到的情况
            if action.get("fail_action") == "abort":
                if root:
                    messagebox.showerror("错误", f"未找到图像: {template_path}，操作中止")
                print(f"未找到图像: {template_path}，操作中止")
                return None
            elif action.get("fail_action") == "skip":
                if root:
                    messagebox.showwarning("警告", f"未找到图像: {template_path}，跳过此步骤")
                print(f"未找到图像: {template_path}，跳过此步骤")
                return "skipped"
            else:
                # 默认继续执行下一个操作
                return "skipped"

    elif action_type == "click":
        # 点击操作
        x = action.get("x")
        y = action.get("y")
        button = action.get("button", "left")
        clicks = action.get("clicks", 1)
        interval = action.get("interval", 0.1)

        # 如果没有提供坐标，则使用上一步找到的坐标
        if x is None and y is None and "last_coordinates" in execute_action.__dict__:
            x, y = execute_action.last_coordinates

        if x is None or y is None:
            print("错误：缺少点击坐标")
            return False

        print(f"步骤: 点击 - 坐标({x}, {y})，按钮:{button}，次数:{clicks}")
        click_mouse(x, y, button, clicks, interval)
        return True

    elif action_type == "type_text":
        # 输入文本
        text = action.get("text", "")
        prefix = text.find("food.")
        if prefix > -1:
            text = config_food.get(textKeyInFoodConfig[prefix+5:])

        interval = action.get("interval", 0.1)

        print(f"步骤: 输入文本 - '{text}'")
        type_text(text, interval)
        return True

    elif action_type == "press_key":
        # 按下按键
        key = action.get("key")

        if not key:
            print("错误：缺少按键参数")
            return False

        print(f"步骤: 按下按键 - {key}")
        press_key(key)
        return True

    elif action_type == "wait":
        # 等待指定时间
        seconds = action.get("seconds", 1.0)

        print(f"步骤: 等待 - {seconds}秒")
        time.sleep(seconds)
        return True

    else:
        print(f"错误：未知操作类型 - {action_type}")
        return False

def load_config(config_path="config.json"):
    """加载配置文件"""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None

def load_config_food(config_path="config-food.json"):
    """加载配置文件"""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None

def save_config(config, config_path="config.json"):
    """保存配置文件"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"配置已保存到 {config_path}")
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

def main():
    """主函数"""
    # 创建Tkinter根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 加载配置
    config = load_config()
    if config is None:
        messagebox.showerror("错误", "无法加载配置文件，程序退出。")
        return

    config_food = load_config_food()
    if config_food is None:
        messagebox.showerror("错误", "无法加载配置文件，程序退出。")
        return

    # 显示配置信息
    config_info = f"配置名称: {config.get('name', '未命名配置')}\n"
    config_info += f"描述: {config.get('description', '无描述')}\n"
    config_info += f"操作步骤数: {len(config.get('actions', []))}\n\n"

    # 确认是否使用配置中的设置
#     use_config = messagebox.askyesno("配置确认",
#                                    f"将执行以下配置:\n\n{config_info}"
#                                    f"是否继续?")
#
#     if not use_config:
#         messagebox.showinfo("操作取消", "程序已取消")
#         return

    # 获取开始前的延迟时间
#     delay = config.get("delay_before_start", 3)
#     messagebox.showinfo("准备开始", f"程序将在 {delay} 秒后开始执行，请确保桌面处于所需状态...")
#     print(f"程序将在 {delay} 秒后开始执行，请确保桌面处于所需状态...")
#     time.sleep(delay)

    # 执行配置中的操作序列
    actions = config.get("actions", [])
    execute_action.last_coordinates = None  # 存储上一步找到的图像坐标

    for i, action in enumerate(actions):
        print(f"\n执行步骤 {i+1}/{len(actions)}:")

        # 执行操作
        result = execute_action(action, root, config_food)

        # 处理执行结果
        if result is None:  # 操作失败并要求中止
            messagebox.showerror("执行错误", f"步骤 {i+1} 执行失败，程序退出")
            return
        elif result == "skipped":  # 操作被跳过
            continue

        # 保存找到的坐标供后续操作使用
        if action.get("type") == "find_image" and result is not None:
            execute_action.last_coordinates = result

#     messagebox.showinfo("操作完成", "已成功执行所有配置的操作！")
    print("操作完成！")

if __name__ == "__main__":
    print("=== 桌面图像查找与鼠标定位程序 ===")
    print("请确保已安装以下依赖库：")
    print("  - opencv-python")
    print("  - pyautogui")
    print("  - pillow")
    print("  - numpy")
    print("=================================")
    main()    