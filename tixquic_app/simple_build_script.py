# -*- coding: utf-8 -*-
"""
無需 psutil 的簡化打包腳本 - 避免環境問題
"""

import os
import subprocess
import shutil
from pathlib import Path
import zipfile
import time
import importlib.util
import sys

class SimpleBuildScript:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.dist_dir = self.project_root / "dist"
        self.website_package_dir = self.project_root / "website_download"
        
        print(f"📁 項目根目錄: {self.project_root}")
        print(f"📁 源代碼目錄: {self.src_dir}")
        
        # 檢測已安裝的套件
        self.available_packages = self._detect_packages()
        
    def _detect_packages(self):
        """檢測已安裝的套件"""
        print("\n🔍 檢測已安裝的套件...")
        
        packages_to_check = [
            'requests',
            'openai', 
            'selenium',
            'playwright',
            'tkinter'
        ]
        
        available = {}
        
        for package in packages_to_check:
            try:
                if package == 'tkinter':
                    import tkinter
                    available[package] = True
                    print(f"   ✅ {package}")
                else:
                    spec = importlib.util.find_spec(package)
                    if spec is not None:
                        available[package] = True
                        print(f"   ✅ {package}")
                    else:
                        available[package] = False
                        print(f"   ❌ {package} (未安裝)")
            except ImportError:
                available[package] = False
                print(f"   ❌ {package} (未安裝)")
        
        return available
    
    def simple_clean_and_prepare(self):
        """簡單清理並準備環境"""
        print("\n🧹 清理舊檔案...")
        
        # 嘗試多次刪除，避免檔案佔用問題
        max_attempts = 3
        
        for directory in [self.dist_dir, self.website_package_dir]:
            if directory.exists():
                for attempt in range(max_attempts):
                    try:
                        shutil.rmtree(directory)
                        print(f"✅ 成功刪除: {directory}")
                        break
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            print(f"⚠️ 第 {attempt + 1} 次刪除失敗，等待 2 秒後重試...")
                            time.sleep(2)
                        else:
                            print(f"❌ 無法刪除目錄: {directory}")
                            print(f"錯誤: {e}")
                            print("\n💡 請手動操作:")
                            print("1. 關閉檔案總管中的相關資料夾")
                            print("2. 關閉任何正在運行的 TixQuic_Grabber.exe")
                            print("3. 關閉 VS Code")
                            input("完成後按 Enter 繼續...")
                            
                            # 最後一次嘗試
                            try:
                                shutil.rmtree(directory)
                                print(f"✅ 手動清理後成功刪除: {directory}")
                            except Exception as final_e:
                                print(f"❌ 仍然無法刪除，請確認所有程式都已關閉")
                                raise final_e
            
            # 創建新目錄
            directory.mkdir(exist_ok=True)
        
        print("✅ 環境準備完成")
    
    def install_missing_packages(self):
        """安裝缺失的套件"""
        print("\n📦 檢查並安裝缺失的套件...")
        
        required_packages = ['requests', 'openai']
        browser_packages = ['selenium']
        
        missing_required = []
        missing_browser = []
        
        for pkg in required_packages:
            if not self.available_packages.get(pkg, False):
                missing_required.append(pkg)
        
        for pkg in browser_packages:
            if not self.available_packages.get(pkg, False):
                missing_browser.append(pkg)
        
        # 安裝缺失的必需套件
        if missing_required:
            print(f"🔧 安裝缺失的必需套件: {', '.join(missing_required)}")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_required, check=True)
                print("✅ 必需套件安裝完成")
                for pkg in missing_required:
                    self.available_packages[pkg] = True
            except subprocess.CalledProcessError as e:
                print(f"❌ 套件安裝失敗: {e}")
                return False
        
        # 確保至少有一個瀏覽器控制套件
        if all(not self.available_packages.get(pkg, False) for pkg in browser_packages):
            print("🔧 安裝瀏覽器控制套件...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'selenium'], check=True)
                print("✅ Selenium 安裝完成")
                self.available_packages['selenium'] = True
            except subprocess.CalledProcessError as e:
                print(f"❌ Selenium 安裝失敗: {e}")
                return False
        
        return True
    
    def compile_simple_version(self):
        """簡單編譯"""
        print("\n🔨 開始編譯...")
        
        main_file = self.src_dir / "main.py"
        if not main_file.exists():
            print(f"❌ 找不到主檔案: {main_file}")
            return False
        
        # 基本編譯參數
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            f"--output-dir={self.dist_dir}",
            "--output-filename=TixQuic_Grabber.exe",
            "--assume-yes-for-downloads",
            "--windows-console-mode=disable",
            "--remove-output",
            str(main_file)
        ]
        
        # 根據可用套件添加包含
        if self.available_packages.get('tkinter', False):
            cmd.append("--include-package=tkinter")
        
        if self.available_packages.get('requests', False):
            cmd.append("--include-package=requests")
        
        if self.available_packages.get('openai', False):
            cmd.append("--include-package=openai")
        
        if self.available_packages.get('selenium', False):
            cmd.append("--include-package=selenium")
        
        if self.available_packages.get('playwright', False):
            cmd.append("--include-package=playwright")
        
        # 基本優化
        optimization_options = [
            "--lto=yes",
            "--enable-plugin=anti-bloat",
            "--nofollow-import-to=pytest",
            "--nofollow-import-to=unittest"
        ]
        cmd.extend(optimization_options)
        
        # 添加圖標
        icon_path = self.src_dir / "assets" / "icon.ico"
        if icon_path.exists():
            cmd.append(f"--windows-icon-from-ico={icon_path}")
        
        print("🚀 開始編譯...")
        print("📋 特性: 簡化版本 + 避免環境衝突")
        print("⏰ 預計時間: 15-20 分鐘")
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, cwd=self.project_root, check=True)
            
            end_time = time.time()
            compile_time = (end_time - start_time) / 60
            print(f"✅ 編譯完成 (耗時: {compile_time:.1f} 分鐘)")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 編譯失敗: {e}")
            print("\n🔧 可能的解決方案:")
            print("1. 確認已安裝 nuitka: pip install nuitka")
            print("2. 確認所有必要套件已安裝")
            print("3. 嘗試重新啟動命令提示字元")
            return False
    
    def create_simple_launcher_scripts(self):
        """創建簡單啟動腳本"""
        print("🚀 創建啟動腳本...")
        
        # 檢測功能
        has_selenium = self.available_packages.get('selenium', False)
        has_playwright = self.available_packages.get('playwright', False)
        has_openai = self.available_packages.get('openai', False)
        
        feature_list = []
        if has_playwright and has_selenium:
            feature_list.append("✅ 雙重瀏覽器支援")
        elif has_selenium:
            feature_list.append("✅ Selenium 瀏覽器控制")
        elif has_playwright:
            feature_list.append("✅ Playwright 瀏覽器控制")
        
        if has_openai:
            feature_list.append("✅ GPT-4 自動驗證碼識別")
        else:
            feature_list.append("🔤 手動驗證碼輸入")
        
        feature_list.extend([
            "✅ 簡化安裝流程",
            "✅ 優化搶票邏輯"
        ])
        
        simple_launcher = f'''@echo off
title TixQuic Grabber - 簡化版
chcp 65001 >nul

echo.
echo     ██████╗ ██╗██╗  ██╗ ██████╗ ██╗   ██╗██╗ ██████╗
echo     ╚══██╔══╝██║╚██╗██╔╝██╔═══██╗██║   ██║██║██╔════╝
echo        ██║   ██║ ╚███╔╝ ██║   ██║██║   ██║██║██║
echo        ██║   ██║ ██╔██╗ ██║▄▄ ██║██║   ██║██║██║
echo        ██║   ██║██╔╝ ██╗╚██████╔╝╚██████╔╝██║╚██████╗
echo        ╚═╝   ╚═╝╚═╝  ╚═╝ ╚══▀▀═╝  ╚═════╝ ╚═╝ ╚═════╝
echo.
echo                   專業搶票助手 v1.0 (簡化版)
echo.
echo     📱 簡化版特性:
{chr(10).join(f"echo     {feature}" for feature in feature_list)}
echo.
echo     📋 使用步驟:
echo     1. 程式將自動啟動
echo     2. 輸入您的驗證碼
echo     3. 點擊"開啟瀏覽器登入"
echo     4. 在瀏覽器中登入您的帳號
echo     5. 返回程式點擊"開始搶票"
echo.
echo     💡 簡化版避免了複雜的環境問題
echo.

cd /d "%~dp0TixQuic_Grabber"
start "" "TixQuic_Grabber.exe"

echo     ✅ 程式已啟動！
timeout /t 3 >nul
'''
        
        launcher_path = self.website_package_dir / "🎯 啟動 TixQuic Grabber (簡化版).bat"
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(simple_launcher)
        
        print("✅ 啟動腳本已創建")
    
    def create_simple_guide(self):
        """創建簡化使用指南"""
        print("📖 創建使用指南...")
        
        has_openai = self.available_packages.get('openai', False)
        
        user_guide = f"""# 🎯 TixQuic Grabber 簡化版使用指南

## 📱 簡化版特性

### ✨ 設計理念
- **簡單易用**: 避免複雜的環境配置問題
- **穩定可靠**: 專注於核心功能的穩定實現
- **零門檻**: 下載即用，無需技術背景

### 🧠 功能特色
{"- **智能驗證碼**: GPT-4 自動識別驗證碼" if has_openai else "- **手動驗證碼**: 安全的手動輸入方式"}
- **精準搶票**: 優化的時間控制和按鈕檢測
- **多重保障**: 完整的錯誤處理和重試機制

## 🚀 快速開始

### 系統需求
- Windows 10 或 Windows 11 (64位元)
- Google Chrome 瀏覽器
- 穩定的網路連接

### 使用步驟

#### 步驟 1: 啟動程式
雙擊 "🎯 啟動 TixQuic Grabber (簡化版).bat"

#### 步驟 2: 輸入驗證碼
在程式視窗中輸入您獲得的驗證碼

#### 步驟 3: 開啟瀏覽器
點擊程式中的 "開啟瀏覽器登入" 按鈕

#### 步驟 4: 登入帳號
在自動開啟的 Chrome 瀏覽器中登入您的拓元帳號

#### 步驟 5: 開始搶票
返回程式，點擊 "開始搶票" 按鈕

## 💡 使用技巧

### 提高成功率
1. **網路準備**: 使用有線網路，確保網路穩定
2. **系統優化**: 關閉不必要的程式釋放資源
3. **瀏覽器準備**: 確保 Chrome 為最新版本
4. **提前登入**: 開搶前 10-15 分鐘完成登入

### 注意事項
- 請確保 Chrome 瀏覽器已安裝
- 搶票過程中請勿關閉瀏覽器
- 保持網路連接穩定

## 🔧 問題排除

### 問題 1: 程式無法啟動
**解決方案**:
- 確認系統為 Windows 10/11 64位元
- 嘗試以管理員身分執行
- 暫時關閉防毒軟體

### 問題 2: 無法連接瀏覽器
**解決方案**:
- 確認已安裝 Google Chrome
- 確認已點擊 "開啟瀏覽器登入"
- 嘗試重新啟動程式

### 問題 3: 驗證碼問題
{"**GPT-4 模式**: 程式會自動識別驗證碼" if has_openai else "**手動模式**: 需要在瀏覽器中手動輸入驗證碼"}
- 識別失敗時會自動重試
- 可在瀏覽器中手動完成驗證碼

## 📊 簡化版優勢

### 相容性
- **環境友好**: 避免複雜的套件衝突
- **安裝簡單**: 無需複雜的環境配置
- **執行穩定**: 專注核心功能，減少出錯

### 效能表現
- **啟動快速**: 優化的啟動流程
- **記憶體使用**: 合理的資源佔用
- **成功率**: 專業級的搶票成功率

## 🛡️ 安全說明

- 程式運行在您的本地電腦
- 不會收集任何個人資料
- 驗證碼處理完全本地化
- 請從官方渠道下載使用

---
🎯 TixQuic Grabber 簡化版
簡單易用，專業可靠！
"""
        
        guide_path = self.website_package_dir / "📖 使用指南 (簡化版).txt"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(user_guide)
        
        print("✅ 使用指南已創建")
    
    def find_compiled_app(self):
        """尋找編譯結果"""
        print("\n🔍 尋找編譯結果...")
        
        possible_locations = [
            self.dist_dir / "main.dist",
            self.dist_dir / "TixQuic_Grabber.dist"
        ]
        
        for location in possible_locations:
            exe_path = location / "TixQuic_Grabber.exe"
            if exe_path.exists():
                print(f"✅ 找到編譯結果: {location}")
                return location
        
        return None
    
    def create_simple_package(self, app_dir):
        """創建簡化版包"""
        print("\n📦 創建簡化版網站下載包...")
        
        # 計算應用大小
        total_size = sum(f.stat().st_size for f in app_dir.rglob('*') if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        print(f"📊 應用大小: {total_size_mb:.1f} MB")
        
        # 複製應用
        download_app_dir = self.website_package_dir / "TixQuic_Grabber"
        shutil.copytree(app_dir, download_app_dir)
        print(f"✅ 應用已複製到: {download_app_dir}")
        
        # 創建腳本和指南
        self.create_simple_launcher_scripts()
        self.create_simple_guide()
        
        # 創建簡化版 ZIP
        zip_path = self.project_root / "TixQuic_Grabber_簡化版_網站下載.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for file_path in self.website_package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.website_package_dir)
                    zipf.write(file_path, arcname)
        
        zip_size = zip_path.stat().st_size / (1024 * 1024)
        print(f"✅ 簡化版 ZIP 已創建: {zip_path}")
        print(f"📦 ZIP 大小: {zip_size:.1f} MB")
        
        return zip_path
    
    def build_simple_package(self):
        """構建簡化版包"""
        print("📱 開始構建簡化版網站下載包...")
        
        # 1. 檢查並安裝套件
        if not self.install_missing_packages():
            print("❌ 套件安裝失敗")
            return False
        
        # 2. 簡單清理準備
        self.simple_clean_and_prepare()
        
        # 3. 簡單編譯
        if not self.compile_simple_version():
            print("❌ 編譯失敗")
            return False
        
        # 4. 尋找編譯結果
        app_dir = self.find_compiled_app()
        if not app_dir:
            print("❌ 找不到編譯結果")
            return False
        
        # 5. 創建簡化版包
        zip_path = self.create_simple_package(app_dir)
        if not zip_path:
            print("❌ 簡化版包創建失敗")
            return False
        
        print("\n🎉 簡化版網站下載包構建完成！")
        print("=" * 60)
        print("📋 簡化版構建結果:")
        print(f"   📁 下載包目錄: {self.website_package_dir}")
        print(f"   📱 簡化版 ZIP: {zip_path}")
        
        print("\n📱 簡化版特性:")
        print("   ✨ 避免複雜的環境問題")
        print("   🚀 簡化的安裝和使用流程")
        print("   💎 專注核心功能的穩定實現")
        print("   🎯 完美適合網站下載分發")
        
        return True

if __name__ == "__main__":
    print("=" * 70)
    print("        📱 TixQuic Grabber 簡化版網站下載構建工具")
    print("=" * 70)
    print("📋 簡化版特色:")
    print("   ✨ 無需 psutil，避免環境衝突")
    print("   🚀 簡化的清理和安裝流程")
    print("   💎 專注穩定性和相容性")
    print("   🎯 零技術門檻，用戶友好")
    print("=" * 70)
    print("\n💡 設計理念: 最大化相容性，最小化複雜度")
    print("⏰ 預計時間: 15-20 分鐘")
    print("🎯 目標: 創建最簡單可靠的網站下載版本")
    
    input("\n按 Enter 鍵開始構建簡化版...")
    
    builder = SimpleBuildScript()
    
    try:
        success = builder.build_simple_package()
        
        if success:
            print("\n🎉 簡化版網站下載構建成功！")
            print("📱 您現在有一個無環境衝突的簡化版本")
            print("✨ 完美適合放到網站供用戶下載")
            print("🎯 用戶體驗簡單，技術門檻為零")
        else:
            print("\n❌ 簡化版構建失敗，請檢查錯誤訊息")
    
    except KeyboardInterrupt:
        print("\n❌ 構建被用戶中斷")
    except Exception as e:
        print(f"\n❌ 構建錯誤: {e}")
    
    input("\n按 Enter 鍵退出...")