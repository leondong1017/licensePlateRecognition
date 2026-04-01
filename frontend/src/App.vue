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
      <div class="nav-user" aria-label="当前用户">
        <span class="nav-user-avatar" aria-hidden="true">A</span>
        <span class="nav-user-name">Abuduuurubulu</span>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>

    <footer class="footer">
      <p>免责声明：识别结果由 AI 生成，仅供参考，不构成法律依据，使用前请人工核实。</p>
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
.nav-links {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
}
.nav-link {
  width: 116px;
  height: 40px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #999;
  text-decoration: none;
  transition: all .15s;
}
.nav-link:hover { color: #ccc; }
.nav-link.active { background: rgba(255,255,255,.12); color: #fff; font-weight: 500; }
.nav-user {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #e8e8e8;
  user-select: none;
}
.nav-user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #6c6c6c, #3f3f3f);
  border: 1px solid rgba(255,255,255,.2);
}
.nav-user-name {
  font-size: 13px;
  font-weight: 500;
  color: #d7d7d7;
}
.main-content { flex: 1; padding: 24px; }
.footer { background: #f0f0f0; border-top: 1px solid #e0e0e0; padding: 14px 24px; }
.footer p { font-size: 11px; color: #999; line-height: 1.7; max-width: 900px; margin: 0 auto; text-align: center; }
.footer strong { color: #bbb; font-weight: 500; }
</style>
