<template>
  <div class="app-shell">
    <header class="nav">
      <div class="nav-brand">
        🚗 车牌识别系统
      </div>
      <nav class="nav-links">
        <router-link to="/" class="nav-link" active-class="active" exact>识别</router-link>
        <router-link to="/history" class="nav-link" active-class="active">历史记录</router-link>
      </nav>
    </header>

    <main class="main-content">
      <router-view />
    </main>

    <footer class="footer">
      <p>
        <strong>免责声明</strong>　本工具仅提供车牌图像识别辅助功能，识别结果由 AI 模型自动生成，可能存在误识别或遗漏，<strong>不构成任何法律证明或执法依据</strong>。用户在将识别结果用于违章举报或其他用途前，须自行核实原始图像信息，并承担相应责任。本平台不存储用户上传的图片，不对识别结果的准确性作出保证。
      </p>
    </footer>
  </div>
</template>

<script setup lang="ts">
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f5f5; color: #1a1a1a; }
</style>

<style scoped>
.app-shell { min-height: 100vh; display: flex; flex-direction: column; }
.nav { background: #1a1a1a; height: 56px; display: flex; align-items: center; padding: 0 24px; gap: 32px; position: sticky; top: 0; z-index: 100; }
.nav-brand { font-size: 15px; font-weight: 600; color: #fff; display: flex; align-items: center; gap: 8px; }
.nav-links { display: flex; gap: 4px; }
.nav-link { padding: 6px 16px; border-radius: 4px; font-size: 13px; color: #999; text-decoration: none; transition: all .15s; }
.nav-link:hover { color: #ccc; }
.nav-link.active { background: rgba(255,255,255,.12); color: #fff; font-weight: 500; }
.main-content { flex: 1; padding: 24px; }
.footer { background: #f0f0f0; border-top: 1px solid #e0e0e0; padding: 14px 24px; }
.footer p { font-size: 11px; color: #999; line-height: 1.7; max-width: 900px; margin: 0 auto; text-align: center; }
.footer strong { color: #bbb; font-weight: 500; }
</style>
